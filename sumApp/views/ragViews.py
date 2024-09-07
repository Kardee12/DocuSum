import json
import os
import re
import tempfile

import langchain_core
import nest_asyncio
import redis
from allauth.socialaccount.models import SocialAccount
from decouple import config
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from dotenv import load_dotenv
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, AsyncChromiumLoader, JSONLoader, UnstructuredCSVLoader, \
    TextLoader, OnlinePDFLoader
from langchain_community.document_transformers import Html2TextTransformer
from langchain_community.vectorstores.chroma import Chroma
from langchain_community.vectorstores.utils import filter_complex_metadata
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from urlextract import URLExtract

from sumApp.models import Document, ChatData
from sumApp.utils.LLMAPIs import formatChatHistory, saveChatMessage

load_dotenv()

global retriever
global vectorstore
r = redis.Redis(host='localhost', port=6379, decode_responses=True)

@login_required
def chatView(request):
    api_key = config('OPENAI_API_KEY')
    social_account = SocialAccount.objects.filter(user=request.user).first()
    avatar_url = None
    if social_account:
        avatar_url = social_account.extra_data.get('picture', None)
    return render(request, 'sumApp/Authenticated/new-chat.html', {'avatar_url': avatar_url, 'api_key': api_key})


@never_cache
@csrf_exempt
@login_required
def processMessagesAndFilesNew(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=400)
    response_data = {}
    message = request.POST.get('message', None)
    files = request.FILES
    retriever = None
    extractor = URLExtract()
    urls = []
    llm = ChatOpenAI(model_name="gpt-4-1106-preview", temperature=0, api_key=config('OPENAI_API_KEY'))
    pages = None
    urls_in_message = []
    files_processed = []
    links_scraped = []
    print(r.ping)
    files_metadata = processFiles(request, files) if files else []
    num_docs_to_use = extract_number_from_request(message)
    if num_docs_to_use:
        selected_files_metadata = files_metadata[-num_docs_to_use:]
    else:
        selected_files_metadata = files_metadata
    try:
        print(message)
        if message:
            # Check if message contains link to parse
            urls_in_message = extractor.find_urls(message)
            for url in urls_in_message:
                if ".pdf" in url:
                    loader = OnlinePDFLoader(url)
                    text_splitter = CharacterTextSplitter(chunk_size=512, chunk_overlap=200)
                    pages = loader.load_and_split(text_splitter)
                else:
                    links = [url]
                    nest_asyncio.apply()
                    loader = AsyncChromiumLoader(links)
                    docs = loader.load()
                    html2text = Html2TextTransformer()
                    docs_transformed = html2text.transform_documents(docs)
                    text_splitter = CharacterTextSplitter(chunk_size=512, chunk_overlap=0)
                    pages = text_splitter.split_documents(docs_transformed)
                setRedis(pages, url)

            document_counter_key = 'document_counter'
            document_count = int(r.get(document_counter_key) or 0)
            retrieved_documents = []
            if document_count != 0:
                for idx in range(document_count):
                    doc_json = r.get(f'document:{idx}')
                    if doc_json:
                        doc_dict = json.loads(doc_json)
                        doc = langchain_core.documents.Document(page_content=doc_dict['page_content'],
                                                                metadata=doc_dict['metadata'])
                        retrieved_documents.append(doc)
                    else:
                        print(f"Document {idx} was not found in Redis.")
                    vectorstore = Chroma.from_documents(documents=retrieved_documents, embedding=OpenAIEmbeddings())
            else:
                pass
            retriever = None

            def contextFunction(question):
                context_parts = []
                if len(retrieved_documents) > 0:
                    retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 2})
                    retrieved_docs = retriever.get_relevant_documents(question)
                    for idx, doc in enumerate(retrieved_docs, start=0):
                        doc_header = f"---Document {idx} ({doc.metadata['source']})---"
                        doc_content = doc.page_content
                        context_parts.append(f"{doc_header}\n{doc_content}")

                chat_history_header = "---CONVERSATION HISTORY---"
                chat_history_content = formatChatHistory(
                    ChatData.objects.filter(user=request.user).order_by('created_at'))
                context_parts.append(f"{chat_history_header}\n{chat_history_content}")
                final_context = "\n\n".join(context_parts)
                print(final_context)
                return final_context

            qa_system_prompt = """
                    You are an assistant for question-answering tasks and your name is DocuSum.
                    Use the following pieces of retrieved context to answer the question or help them perform tasks..
                    Use three sentences maximum and keep the answer concise. Chat History is included in the context as well.
                    If an user asks for chat history, you will only give the chat history and nothing else.
                    Include the document source as well when you answer a question from a document.
                    If an user provides an URL, do not say you cannot access external content, since that URL would be transcribed into a document.
                    When an user says to retrieve data from a document, use the document metadata name to figure what document to retrieve it from.
                    When an user says to retrieve date from multiple documents by the name of their pdf, use data from both documents.
                    {context}
                """
            qa_prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", qa_system_prompt),
                    ("human", "{question}"),
                ]
            )
            rag_chain = (
                    RunnablePassthrough.assign(context=lambda x: contextFunction(x["question"]))
                    | qa_prompt
                    | llm
                    | StrOutputParser()

            )
            aiResponse = rag_chain.invoke({"question": message})
            print(aiResponse)
            saveChatMessage(request.user, message, is_question=True, is_ai=False)
            saveChatMessage(request.user, aiResponse, is_question=False, is_ai=True)
            response_data['api_response'] = aiResponse
            return JsonResponse(response_data)

    except Exception as e:
        print(f"An error occurred: {e}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


def extract_number_from_request(request_text):
    match = re.search(r"last (\d+) documents", request_text)
    if match:
        return int(match.group(1))
    return None


def processFiles(request, files):
    processed_files_metadata = []
    summary = []
    for file_key, file in files.items():
        file = request.FILES[file_key]
        print(file)
        origName = file.name
        document = Document(name=origName, file=file)
        document.save()
        sumText = ""
        if file.content_type == 'text/plain':
            with tempfile.NamedTemporaryFile(delete=True) as temp_file:
                for chunk in file.chunks():
                    temp_file.write(chunk)
                temp_file.flush()
                loader = TextLoader(temp_file.name, encoding='utf-8')
                text_splitter = CharacterTextSplitter(chunk_size=512, chunk_overlap=200)
                pages = loader.load_and_split(text_splitter)
                setRedis(pages, origName)
        if file.content_type == 'application/pdf':
            with tempfile.NamedTemporaryFile(delete=True) as temp_file:
                for chunk in file.chunks():
                    temp_file.write(chunk)
                temp_file.flush()
                loader = PyPDFLoader(temp_file.name, extract_images=True)
                text_splitter = CharacterTextSplitter(chunk_size=512, chunk_overlap=200)
                pages = loader.load_and_split(text_splitter)
                setRedis(pages, origName)
        if file.content_type == 'text/csv':
            with tempfile.NamedTemporaryFile(delete=True) as temp_file:
                for chunk in file.chunks():
                    temp_file.write(chunk)
                temp_file.flush()
                loader = UnstructuredCSVLoader(
                    file_path=temp_file.name, mode="elements"
                )
                df = loader.load()
                pages = filter_complex_metadata(df)
                setRedis(pages, origName)
        if file.content_type == 'application/json':
            with tempfile.NamedTemporaryFile(delete=True) as temp_file:
                for chunk in file.chunks():
                    temp_file.write(chunk)
                temp_file.flush()
                loader = JSONLoader(temp_file, jq_schema='.')
                text_splitter = CharacterTextSplitter(chunk_size=512, chunk_overlap=200)
                pages = loader.load_and_split(text_splitter)
                setRedis(pages, origName)
        file_path = document.file.path
        if os.path.isfile(file_path):
            os.remove(file_path)
        processed_files_metadata.append({
            'original_name': origName,
            'document_name': file.name,
        })
    return processed_files_metadata


def setRedis(pages, file_name_or_title):
    document_counter_key = 'document_counter'
    current_count = int(r.get(document_counter_key) or 0)

    for idx, page in enumerate(pages, start=current_count):
        metadata = {
            'source': file_name_or_title,
            'page': idx - current_count + 1
        }

        doc_dict = {
            'page_content': page.page_content,
            'metadata': metadata
        }
        r.set(f'document:{idx}', json.dumps(doc_dict))
        r.incr(document_counter_key)

@csrf_exempt
@login_required
def clearChat(request):
    if request.method == 'POST':
        r.flushall()
        ChatData.objects.filter(user=request.user).delete()
        conv_history = ChatData.objects.filter(user=request.user)
        context = "Previous Chat history has been cleared. Everything is now new after this line\n"
        context += ",".join([content.content for content in conv_history])
        print('New history is {' + str(context) + '}')
        retriever = None
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)