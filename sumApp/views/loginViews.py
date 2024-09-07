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
