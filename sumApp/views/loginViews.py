from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from allauth.socialaccount.models import SocialAccount
from django.contrib import messages


@login_required
def profile(request):
    try:
        social_account = SocialAccount.objects.get(user=request.user)
    except SocialAccount.DoesNotExist:
        social_account = None
    # Sign Out User
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
    logout(request)
    return redirect('/logout')