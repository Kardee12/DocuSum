from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .views import normalViews, loginViews

urlpatterns = [
    path("", normalViews.index, name = 'index'),
    path("workspace", normalViews.workspace, name ='workspace'),
    path("profile/", loginViews.profile, name = 'profile'),
    path("login/", normalViews.logView, name='login'),
    path('custom-logout/', loginViews.custom_logout, name = 'custom_logout'),
    path('logout/', loginViews.logoutView, name = 'logout'),
    path("editor", loginViews.editor, name = 'editor'),
    path("dashboard/", loginViews.dashboard, name='dashboard')
]+ static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)