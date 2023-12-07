import tempfile

import textract
from django.core.files.uploadedfile import InMemoryUploadedFile
from tika import parser

from sumApp.utils.HuggingFaceAPIs import huggingFaceAPis


class TextExtractor:
    def extract(self, file):
        if isinstance(file, InMemoryUploadedFile):
            with tempfile.NamedTemporaryFile(delete = False) as temp_file:
                temp_file.write(file.read())
                if file.name.endswith('.pdf'):
                    pdf = parser.from_file(temp_file.name)
                    text = pdf['content']
                elif file.name.endswith('.docx'):
                    text = textract.process(temp_file.name)
                else:
                    text = file.read().decode('utf-8', errors = 'ignore')
        else:
            raise FileNotFoundError
        return text.strip()


class TextSummarization:

    def pickModel(self, model_name, text, maxTokens, minTokens):
        model = model_name.upper()
        hFace = huggingFaceAPis()
        output = hFace.sumQuery(model, text, maxTokens, minTokens)
        if not output:
            return "Error: Can't get a response from the model."
        if model == "BART":
            result = output[0]['summary_text'] if output else ""
        elif model == "FLAN-T5":
            result = output[0]['generated_text'] if output else ""
        else:
            result = ""

        return result


class TextTranslation:

    def pickModel(self, model_name, text, langTTF, langTTT):
        model = model_name.upper()
        hFace = huggingFaceAPis()
        print("Translating")
        output = hFace.transQuery(model, text, langTTF, langTTT)
        print(langTTF)
        print(output)
        result = output[0]['translation_text']
        print(result)
        return result


class QuestionAnswering:

    def pickModel(self, model_name, text, question):
        model = model_name.upper()
        hFace = huggingFaceAPis()
        output = hFace.askQuery(model, text, question)
        print(output)
        return output


class SentimentAnalysis:
    def pickModel(self, model_name, text):
        model = model_name.upper()
        hFace = huggingFaceAPis()
        output = hFace.sentimentQuery(model, text)
        return output
