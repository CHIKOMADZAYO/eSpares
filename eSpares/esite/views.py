from django.shortcuts import render,redirect
from django.contrib.auth import authenticate, login

# Create your views here.

def home(request):
    return render(request, 'site/base.html')


def login_view(request):
    if request.method == 'POST':
        pass
    return render(request, 'site/login.html')