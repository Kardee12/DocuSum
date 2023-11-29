import csv
from io import StringIO

from allauth.socialaccount.models import SocialAccount
from decouple import config
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from dotenv import load_dotenv
from langchain.chat_models import ChatOpenAI
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores.chroma import Chroma

from sumApp.forms import TranslationForm, SummarizationForm, QuestionForm, SentimentAnalysisForm
from sumApp.models import ChatData
from sumApp.models import Document
from sumApp.service import TextExtractor, TextSummarization, QuestionAnswering, SentimentAnalysis, TextTranslation
from sumApp.utils.LLMAPIs import extract_text_from_pdf, \
    saveChatMessage, getChatHistory, format_chat_history

load_dotenv()


@login_required
def profile(request):
    try:
        social_account = SocialAccount.objects.get(user = request.user)
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
        ChatData.objects.filter(user = request.user).delete()

    # Then logout the user
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
    if request.method == 'POST' and 'action' in request.POST:
        if request.POST['action'] == 'summarize':
            active = 'summarize'
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
                    sumSuccessMessage = "Summary Successfully Generated"
                    sumForm = SummarizationForm()

        if request.POST['action'] == 'translate':
            active = 'translate'
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
                    trSuccessMessage = "Translation Successfully Generated"
                    sumForm = SummarizationForm()

        if request.POST['action'] == 'ask':
            active = 'ask'
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
                print(text)
                original = text
                if result:
                    qaSuccessMessage = "Question Successfully Answered"
                    sumForm = SummarizationForm()

        if request.POST['action'] == 'sentiment':
            active = 'sentiment'
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


@csrf_exempt
@login_required
def processMessagesAndFiles(request):
    if request.method == 'POST':
        response_data = {}
        message = request.POST.get('message')
        file = request.FILES.get('file')
        link = request.POST.get('link')
        llm = ChatOpenAI(model_name = "gpt-4-1106-preview", temperature = 0)
        global retriever
        conversation_memory = ConversationBufferMemory(memory_key = "chat_history")
        if file:
            document = Document(name = 'tmp', file = file)
            document.save()
            text = ""
            print(file.content_type)
            if file.content_type == 'text/plain':
                document.file.open('r')
                file_content = document.file.read()
                if isinstance(file_content, bytes):
                    text = file_content.decode('utf-8', errors = 'ignore')
                else:
                    text = file_content
                document.file.close()
            if file.content_type == 'application/pdf':
                text = extract_text_from_pdf(document.id)
                document.file.close()
            elif file.content_type == 'text/csv':
                document.file.open('r')
                csv_file = StringIO(document.file.read())
                reader = csv.reader(csv_file)
                text = ' '.join([' '.join(row) for row in reader])
                document.file.close()
            if text:
                text_splitter = CharacterTextSplitter(chunk_size = 512, chunk_overlap = 200)
                texts = text_splitter.create_documents([text])
                vectorstore = Chroma.from_documents(documents = texts, embedding = OpenAIEmbeddings())
                retriever = vectorstore.as_retriever(search_type = "similarity", search_kwargs = {"k": 6})
            document.delete()
        if link:
            print(link)
        if message:
            chat_history_qs = ChatData.objects.filter(user = request.user).order_by('created_at')
            formatted_history = format_chat_history(chat_history_qs)

            def context_function(question):
                retrieved_docs = retriever.get_relevant_documents(question)
                docs_context = "\n\n".join(doc.page_content for doc in retrieved_docs)
                return f"Here is the conversation history:\n{formatted_history}\n\n{docs_context}"

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
                    RunnablePassthrough.assign(context = lambda x: context_function(x["question"]))
                    | qa_prompt
                    | llm
                    | StrOutputParser()
            )
            ai_response = rag_chain.invoke({"question": message})
            saveChatMessage(request.user, message, is_question = True, is_ai = False)
            saveChatMessage(request.user, ai_response, is_question = False, is_ai = True)
            response_data['api_response'] = ai_response

        return JsonResponse(response_data)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status = 400)


@csrf_exempt
@login_required
def clearChat(request):
    if request.method == 'POST':
        ChatData.objects.filter(user = request.user).delete()
        conv_history = ChatData.objects.filter(user = request.user)
        context = ",".join([content.content for content in conv_history])
        print('New history is {' + str(context) + '}')
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status = 400)
