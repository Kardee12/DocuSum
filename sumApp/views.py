from django.shortcuts import render
from .forms import TranslationForm, SummarizationForm, QuestionForm, SentimentAnalysisForm
from .service import TextSummarization, TextExtractor, TextTranslation, QuestionAnswering, SentimentAnalysis


def index(request):
    return render(request, "sumApp/index.html")


def about(request):
    return render(request, "sumApp/about.html")


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
    saSuccessMessage =""
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
                result = asker.pickModel(model, text)
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

    return render(request, 'sumApp/workspace.html', context)
