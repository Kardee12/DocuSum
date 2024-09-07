import tempfile
import urllib

import fitz
from django.core.files.uploadedfile import InMemoryUploadedFile
from dotenv import load_dotenv

from sumApp.models import ChatData, Document

load_dotenv()


def getContext(user):
    context_entries = ChatData.objects.filter(user=user, isAI=False, isQuestion=False).order_by('-created_at')
    context = " ".join([entry.content for entry in context_entries])
    return context


def ensure_https_www(url):
    decoded_url = urllib.parse.unquote(url)
    if not (decoded_url.startswith("http://") or decoded_url.startswith("https://")):
        decoded_url = "https://www." + decoded_url

    return decoded_url


def handleUploadedFile(uploaded_file: InMemoryUploadedFile):
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, mode='wb+', suffix=".pdf") as temp_file:
            for chunk in uploaded_file.chunks():
                temp_file.write(chunk)
            temp_path = temp_file.name
    except Exception as e:
        print(f"Error while handling uploaded file: {e}")
    return temp_path


def handle_uploaded_file(f):
    with open('temp/', 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)
    return f.path


def extract_text_from_pdf(document_id):
    try:
        document = Document.objects.get(id=document_id)
        text = ""
        with fitz.open(document.file.path) as doc:
            for page in doc:
                text += page.get_text()
        return text
    except Document.DoesNotExist:
        print(f"Document with id {document_id} does not exist.")
        return None
    except Exception as e:
        print(f"An error occurred while extracting text: {e}")
        return None


def saveChatMessage(user, content, is_question, is_ai):
    chat_message = ChatData(
        user=user,
        content=content,
        isQuestion=is_question,
        isAI=is_ai
    )
    chat_message.save()


def getChatHistory(user):
    return ChatData.objects.filter(user=user).order_by('created_at')


def formatChatHistory(messages):
    formatted_history = ""
    for entry in messages:
        speaker = "User" if entry.isQuestion else "AI"
        formatted_history += f"{speaker}: {entry.content}\n"
    return formatted_history.strip()
