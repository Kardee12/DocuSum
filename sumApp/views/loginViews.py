import json
import json
import re
import tempfile

import langchain_core.documents
import nest_asyncio
import redis
from allauth.socialaccount.models import SocialAccount
from decouple import config
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from dotenv import load_dotenv
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores.chroma import Chroma
from langchain_community.document_loaders import AsyncChromiumLoader
from langchain_community.document_loaders import PyPDFLoader, UnstructuredCSVLoader
from langchain_community.document_loaders import TextLoader, JSONLoader
from langchain_community.document_transformers import Html2TextTransformer
from langchain_community.vectorstores.utils import filter_complex_metadata
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from transformers import pipeline
from sumApp.forms import TranslationForm, SummarizationForm, QuestionForm, SentimentAnalysisForm
from sumApp.models import ChatData
from sumApp.models import Document
from sumApp.service import TextExtractor, TextSummarization, QuestionAnswering, SentimentAnalysis, TextTranslation
from sumApp.utils.LLMAPIs import saveChatMessage, formatChatHistory
from urlextract import URLExtract

load_dotenv()

global retriever
r = redis.Redis(host='localhost', port=6379, decode_responses=True)
model_name = "ThomasSimonini/t5-end2end-question-generation"

@login_required
def profile(request):
    try:
        social_account = SocialAccount.objects.get(user=request.user)
    except SocialAccount.DoesNotExist:
        social_account = None
    if 'sign_out' in request.POST:
        logout(request)
        return redirect('index')
    if 'delete_account' in request.POST:
        request.user.delete()
        return redirect('index')

    return render(request, 'sumApp/Authenticated/profile.html', {
        'social_account': social_account
    })


def editor(request):
    return render(request, 'sumApp/Authenticated/editor.html')


@login_required()
def dashboard(request):
    return render(request, 'sumApp/Authenticated/dashboard.html', {'user': request.user})


def logoutView(request):
    return render(request, 'sumApp/logout.html')


def custom_logout(request):
    if request.user.is_authenticated:
        ChatData.objects.filter(user=request.user).delete()
    logout(request)
    return redirect('/logout')


@login_required()
def workspace(request):
    sumForm = SummarizationForm()
    tranForm = TranslationForm()
    quesForm = QuestionForm()
    sentiForm = SentimentAnalysisForm()
    result = ""
    original = ""
    sumSuccessMessage = ""
    trSuccessMessage = ""
    qaSuccessMessage = ""
    saSuccessMessage = ""
    active = "summarize"
    currAction = ""
    if request.method == 'POST' and 'action' in request.POST:
        if request.POST['action'] == 'summarize':
            active = 'summarize'
            currAction = 'summarize'
            sumForm = SummarizationForm(request.POST, request.FILES)
            if sumForm.is_valid():
                text = sumForm.cleaned_data['textInput']
                model = sumForm.cleaned_data['model']
                minTokens = sumForm.cleaned_data['minTokens']
                maxTokens = sumForm.cleaned_data['maxTokens']
                if sumForm.cleaned_data['uploadFile']:
                    uploadFile = request.FILES['uploadFile']
                    print(len(uploadFile))
                    print("The type is" + str(type(uploadFile)))
                    extractor = TextExtractor()
                    text = extractor.extract(uploadFile)
                print(text)
                summarizer = TextSummarization()
                result = summarizer.pickModel(model, text, maxTokens, minTokens)
                original = text
                if result:
                    request.session['original'] = original
                    request.session['result'] = result
                    request.session['recentAction'] = currAction
                    request.session['actionCompleted'] = True
                    sumSuccessMessage = "Summary Successfully Generated"
                    sumForm = SummarizationForm()

        if request.POST['action'] == 'translate':
            active = 'translate'
            currAction = 'translate'
            tranForm = TranslationForm(request.POST, request.FILES)
            if tranForm.is_valid():
                text = tranForm.cleaned_data['textInput']
                model = tranForm.cleaned_data['model']
                langTTF = tranForm.cleaned_data['langTTF']
                langTTT = tranForm.cleaned_data['langTTT']
                if tranForm.cleaned_data['uploadFile']:
                    uploadFile = request.FILES['uploadFile']
                    print(len(uploadFile))
                    print("The type is" + str(type(uploadFile)))
                    extractor = TextExtractor()
                    text = extractor.extract(uploadFile)
                translator = TextTranslation()
                result = translator.pickModel(model, text, langTTF, langTTT)
                print(result)
                original = text
                if result:
                    request.session['original'] = original
                    request.session['result'] = result
                    request.session['recentAction'] = currAction
                    request.session['actionCompleted'] = True
                    trSuccessMessage = "Translation Successfully Generated"
                    sumForm = SummarizationForm()

        if request.POST['action'] == 'ask':
            active = 'ask'
            currAction = 'question'

            quesForm = QuestionForm(request.POST, request.FILES)
            if quesForm.is_valid():
                text = quesForm.cleaned_data['textInput']
                model = quesForm.cleaned_data['model']
                question = quesForm.cleaned_data['question']
                if quesForm.cleaned_data['uploadFile']:
                    uploadFile = request.FILES['uploadFile']
                    print(len(uploadFile))
                    print("The type is" + str(type(uploadFile)))
                    extractor = TextExtractor()
                    text = extractor.extract(uploadFile)
                asker = QuestionAnswering()
                result = asker.pickModel(model, text, question)
                result = result['answer'].replace('\n', ' ')
                original = text
                if result:
                    request.session['original'] = original
                    request.session['result'] = result
                    request.session['recentAction'] = currAction
                    request.session['actionCompleted'] = True
                    qaSuccessMessage = "Question Successfully Answered"
                    sumForm = SummarizationForm()

        if request.POST['action'] == 'sentiment':
            active = 'sentiment'
            currAction = 'sentiment'
            sentiForm = SentimentAnalysisForm(request.POST, request.FILES)
            if sentiForm.is_valid():
                text = sentiForm.cleaned_data['textInput']
                model = sentiForm.cleaned_data['model']
                if sentiForm.cleaned_data['uploadFile']:
                    uploadFile = request.FILES['uploadFile']
                    print(len(uploadFile))
                    print("The type is" + str(type(uploadFile)))
                    extractor = TextExtractor()
                    text = extractor.extract(uploadFile)
                senti = SentimentAnalysis()
                result = senti.pickModel(model, text)
                print(text)
                original = text
                if result:
                    request.session['original'] = original
                    request.session['result'] = result
                    request.session['recentAction'] = currAction
                    request.session['actionCompleted'] = True
                    qaSuccessMessage = "Sentiment Analysis Done"
                    sentiForm = SentimentAnalysisForm()
    context = {
        'sumForm': sumForm,
        'tranForm': tranForm,
        'quesForm': quesForm,
        'sentiForm': sentiForm,
        'original': original,
        'result': result,
        'sumSuccessMessage': sumSuccessMessage if result else "",
        'trSuccessMessage': trSuccessMessage if result else "",
        'qaSuccessMessage': qaSuccessMessage if result else "",
        'saSuccessMessage': saSuccessMessage if result else "",
        'active': active
    }

    return render(request, 'sumApp/Authenticated/workspace.html', context)


@login_required()
def chat_view(request):
    api_key = config('OPENAI_API_KEY')
    print(f"API Key: {api_key}")
    return render(request, 'sumApp/Authenticated/chat.html')


@login_required
def testView(request):
    api_key = config('OPENAI_API_KEY')
    social_account = SocialAccount.objects.filter(user=request.user).first()
    avatar_url = None
    if social_account:
        # Assuming the profile picture URL is stored under 'picture' in the extra_data
        avatar_url = social_account.extra_data.get('picture', None)
    return render(request, 'sumApp/Authenticated/new-chat.html', {'avatar_url': avatar_url, 'api_key': api_key})


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
                    If an user asks for chat history, you will only give the chat history and nothing else.
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
                # print(pages)
        if file.content_type == 'text/csv':
            # PANDAS DATAFRAME AS WELL MAYBE USE DATAFRAMELOADER
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

@csrf_exempt
@login_required
def processMessagesAndFiles(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=400)
    response_data = {}
    message = request.POST.get('message')
    file = request.FILES.get('file')
    link = request.POST.get('link')
    retriever = None
    llm = ChatOpenAI(model_name="gpt-4-1106-preview", temperature=0)
    pages = None
    print(r.ping())
    try:
        if file:
            document = Document(name='tmp', file=file)
            document.save()
            text = ""
            if file.content_type == 'text/plain':
                with tempfile.NamedTemporaryFile(delete=True) as temp_file:
                    for chunk in file.chunks():
                        temp_file.write(chunk)
                    temp_file.flush()
                    loader = TextLoader(temp_file.name, encoding='utf-8')
                    text_splitter = CharacterTextSplitter(chunk_size=512, chunk_overlap=200)
                    pages = loader.load_and_split(text_splitter)
                    # print(pages)
            if file.content_type == 'application/pdf':
                with tempfile.NamedTemporaryFile(delete=True) as temp_file:
                    for chunk in file.chunks():
                        temp_file.write(chunk)
                    temp_file.flush()
                    loader = PyPDFLoader(temp_file.name, extract_images=True)
                    text_splitter = CharacterTextSplitter(chunk_size=512, chunk_overlap=200)
                    pages = loader.load_and_split(text_splitter)
                    # print(pages)
            if file.content_type == 'text/csv':
                # PANDAS DATAFRAME AS WELL MAYBE USE DATAFRAMELOADER
                with tempfile.NamedTemporaryFile(delete=True) as temp_file:
                    for chunk in file.chunks():
                        temp_file.write(chunk)
                    temp_file.flush()
                    loader = UnstructuredCSVLoader(
                        file_path=temp_file.name, mode="elements"
                    )
                    pages = loader.load()
                    pages = filter_complex_metadata(pages)
            if file.content_type == 'application/json':
                with tempfile.NamedTemporaryFile(delete=True) as temp_file:
                    for chunk in file.chunks():
                        temp_file.write(chunk)
                    temp_file.flush()
                    loader = JSONLoader(temp_file, jq_schema='.')
                    text_splitter = CharacterTextSplitter(chunk_size=512, chunk_overlap=200)
                    pages = loader.load_and_split(text_splitter)
                    # print(pages)
            document.delete()
        if link:
            if ".pdf" in link:
                loader = PyPDFLoader(link, extract_images=True)
                text_splitter = CharacterTextSplitter(chunk_size=512, chunk_overlap=200)
                pages = loader.load_and_split(text_splitter)
            else:
                links = [link]
                nest_asyncio.apply()
                loader = AsyncChromiumLoader(links)
                docs = loader.load()
                html2text = Html2TextTransformer()
                docs_transformed = html2text.transform_documents(docs)
                text_splitter = CharacterTextSplitter(chunk_size=512, chunk_overlap=0)
                pages = text_splitter.split_documents(docs_transformed)
        if pages:
            document_counter_key = 'document_counter'
            r.set(document_counter_key, 0)
            for idx, doc in enumerate(pages):
                r.incr(document_counter_key)
                doc_dict = {
                    'page_content': doc.page_content,
                    'metadata': doc.metadata
                }
                r.set(f'document:{idx}', json.dumps(doc_dict))
        if message:
            print("ARRIVED")
            chatHistory = ChatData.objects.filter(user=request.user).order_by('created_at')
            history = formatChatHistory(chatHistory)
            document_counter_key = 'document_counter'
            document_count = int(r.get(document_counter_key) or 0)
            retrieved_documents = []

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
            retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 6})

            def contextFunction(question):
                documents_info = 'The documents to be questioned on are: ...'
                if retriever is None:
                    return f"{documents_info}\n\nHere is the conversation history:\n{history}"
                retrieved_docs = retriever.get_relevant_documents(question)
                docs_context = "\n\n".join(doc.page_content for doc in retrieved_docs)
                complete_context = f"{documents_info}\n\nHere is the conversation history:\n{history}\n\n{docs_context}"
                print(complete_context)
                return complete_context

            qa_system_prompt = """
                    You are an assistant for question-answering tasks.
                    Use the following pieces of retrieved context to answer the question.
                    If you don't know the answer, just say that you don't know.
                    Use three sentences maximum and keep the answer concise. Chat History is included in the context as well.
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


@login_required
def downloadFile(request):
    original = request.session.get('original', '')
    result = request.session.get('result', '')
    action = request.session.get('recentAction', 'default')
    file_content = f"{original}\n_______\n{action}:\n{result}"
    filename = f"{action}_output.txt"
    response = HttpResponse(file_content, content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    del request.session['original']
    del request.session['result']
    del request.session['recentAction']
    del request.session['actionCompleted']

    return response


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
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)
