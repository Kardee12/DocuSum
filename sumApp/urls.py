from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from .views import normalViews, loginViews

urlpatterns = [
                  path("", normalViews.index, name = 'index'),
                  path("workspace/", loginViews.workspace, name = 'workspace'),
                  path("profile/", loginViews.profile, name = 'profile'),
                  path("login/", normalViews.logView, name = 'login'),
                  path('custom-logout/', loginViews.custom_logout, name = 'custom_logout'),
                  path('logout/', loginViews.logoutView, name = 'logout'),
                  path("editor", loginViews.editor, name = 'editor'),
                  path("dashboard/", loginViews.dashboard, name = 'dashboard'),
                  path('chat/', loginViews.chat_view, name = 'chat_view'),
                  path('processMessagesAndFiles/', loginViews.processMessagesAndFiles,
                       name = 'processMessagesAndFiles'),
                  path('clearChat/', loginViews.clearChat, name = 'clearChat'),
                  path('download/', loginViews.downloadFile, name = 'downloadFile'),
              ] + static(settings.STATIC_URL, document_root = settings.STATIC_ROOT)
