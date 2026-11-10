from django.shortcuts import render,redirect
from django.contrib.auth import authenticate, login

# Create your views here.


def login_view(request):
    if request.method == 'POST':
        pass
    return render(request, 'accounts/login.html')