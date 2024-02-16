import json
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
from django.views.decorators.csrf import csrf_exempt
from dotenv import load_dotenv
from langchain.chains import llm
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, AsyncChromiumLoader, JSONLoader, UnstructuredCSVLoader, \
    TextLoader
from langchain_community.document_transformers import Html2TextTransformer
from langchain_community.vectorstores.chroma import Chroma
from langchain_community.vectorstores.utils import filter_complex_metadata
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from urlextract import URLExtract

from sumApp.models import Document, ChatData
from sumApp.utils.LLMAPIs import formatChatHistory, saveChatMessage
from sumApp.views.loginViews import setRedis

load_dotenv()

global retriever
r = redis.Redis(host='localhost', port=6379, decode_responses=True)


@login_required
def testView(request):
    api_key = config('OPENAI_API_KEY')
    social_account = SocialAccount.objects.filter(user=request.user).first()
    avatar_url = None
    if social_account:
        # Assuming the profile picture URL is stored under 'picture' in the extra_data
        avatar_url = social_account.extra_data.get('picture', None)
    return render(request, 'sumApp/Authenticated/new-chat.html', {'avatar_url': avatar_url, 'api_key': api_key})

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
    llm = ChatOpenAI(model_name="gpt-4-1106-preview", temperature=0)
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
            #Check if message contains link to parse
            urls_in_message = extractor.find_urls(message)
            for url in urls_in_message:
                if ".pdf" in url:
                    loader = PyPDFLoader(url, extract_images=True)
                    text_splitter = CharacterTextSplitter(chunk_size=512, chunk_overlap=200)
                    pages = loader.load_and_split(text_splitter)
                    setRedis(pages, url)
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

            chatHistory = ChatData.objects.filter(user=request.user).order_by('created_at')
            history = formatChatHistory(chatHistory)
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
                        print(doc)
                        retrieved_documents.append(doc)
                    else:
                        print(f"Document {idx} was not found in Redis.")
                    vectorstore = Chroma.from_documents(documents=retrieved_documents, embedding=OpenAIEmbeddings())
            else:
                pass

            retriever = None
            def contextFunction(question):
                if(len(retrieved_documents)> 0):
                    retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 6})
                    documents_info = 'The documents to be questioned on are: ...'
                    retrieved_docs = retriever.get_relevant_documents(question)
                    docs_context = "\n\n".join(doc.page_content for doc in retrieved_docs)
                    return f"{documents_info}\n\nHere is the conversation history:\n{history}\n\n{docs_context}"
                else:
                    return f"\nHere is the conversation history:\n{history}"

            qa_system_prompt = """
                    You are an assistant for question-answering tasks and your name is DocuSum.
                    Use the following pieces of retrieved context to answer the question or help them perform tasks..
                    If you don't know the answer, just say that you don't know.
                    Use three sentences maximum and keep the answer concise. Chat History is included in the context as well.
                    If an user asks for chat history, you will only give the chat history and nothing else. Include the document source as well when you answer a question from a document.
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
    for file_key, file in files.items():
        file = request.FILES[file_key]
        origName = file.name
        document = Document(name='tmp', file=file)
        document.save()
        if file.content_type == 'text/plain':
            with tempfile.NamedTemporaryFile(delete=True) as temp_file:
                for chunk in file.chunks():
                    temp_file.write(chunk)
                temp_file.flush()
                loader = TextLoader(temp_file.name, encoding='utf-8')
                text_splitter = CharacterTextSplitter(chunk_size=512, chunk_overlap=200)
                pages = loader.load_and_split(text_splitter)
                setRedis(pages, document.name)
        if file.content_type == 'application/pdf':
            with tempfile.NamedTemporaryFile(delete=True) as temp_file:
                for chunk in file.chunks():
                    temp_file.write(chunk)
                temp_file.flush()
                loader = PyPDFLoader(temp_file.name, extract_images=True)
                text_splitter = CharacterTextSplitter(chunk_size=512, chunk_overlap=200)
                pages = loader.load_and_split(text_splitter)
                setRedis(pages, document.name)
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
                setRedis(pages, document.name)
        if file.content_type == 'application/json':
            with tempfile.NamedTemporaryFile(delete=True) as temp_file:
                for chunk in file.chunks():
                    temp_file.write(chunk)
                temp_file.flush()
                loader = JSONLoader(temp_file, jq_schema='.')
                text_splitter = CharacterTextSplitter(chunk_size=512, chunk_overlap=200)
                pages = loader.load_and_split(text_splitter)
                setRedis(pages, document.name)
        document.delete()
        processed_files_metadata.append({
            'original_name': origName,
            'document_name': file.name,
        })
    return processed_files_metadata

def setRedis(pages, file_names):
    document_counter_key = 'document_counter'
    current_count = int(r.get(document_counter_key) or 0)

    for idx, (doc, file_name) in enumerate(zip(pages, file_names), start=current_count):
        doc_dict = {
            'page_content': doc.page_content,
            'metadata': doc.metadata,
            'file_name': file_name
        }
        r.set(f'document:{idx}', json.dumps(doc_dict))
        r.incr(document_counter_key)

def extract_document_name_from_request(request_text):
    match = re.search(r"document (named|called) (\w+)", request_text, re.IGNORECASE)
    if match:
        return match.group(2)  # Returns the name of the document
    return None