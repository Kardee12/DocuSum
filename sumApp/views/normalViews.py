from django.shortcuts import render, redirect

from DocuSum import settings


def index(request):
    socialaccount_google_login_by_token = settings.SOCIAL_AUTH_GOOGLE_CLIENT_ID
    context = {
        'socialaccount_google_login_by_token': socialaccount_google_login_by_token,
    }
    return render(request, "sumApp/index.html", context)


def loginRedirect(request):
    # Your logic here, e.g., checking the user profile or redirecting to a dashboard
    return redirect('workspace')


def logView(request):
    return render(request, 'sumApp/login.html')
