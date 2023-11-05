from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path("", views.index, name = 'index'),
    path("about", views.about, name = 'about'),
    path("workspace", views.workspace, name ='workspace'),

]+ static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)