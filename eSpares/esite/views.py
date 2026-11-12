from django.contrib.auth import authenticate, get_user_model, login, logout
from django.shortcuts import redirect, render
from .models import Product
from .form import UserRegistrationForm,ProductForm, UserLoginForm


# Create your views here.

def home(request):
    return render(request, 'base.html')





def login_view(request):
    # get the login form
    login_form = UserLoginForm(request.POST or None)

    if request.method == 'POST' and login_form.is_valid():
        username = login_form.cleaned_data['username']
        password = login_form.cleaned_data['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            login_form.add_error(None, 'Invalid username or password.')

    return render(request, 'login.html', {'form': login_form})


def signup_view(request):
    form = UserRegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user_model = get_user_model()
        username = form.cleaned_data['username']
        if user_model.objects.filter(username=username).exists():
            form.add_error('username', 'A user with that username already exists.')
        else:
            user = user_model.objects.create_user(
                username=username,
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password1'],
            )
            login(request, user)
            return redirect('home')
    return render(request, 'signup.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('home')



def create_product(request):
    pass  # Placeholder for product creation logic



def product_list(request):
    pass  # Placeholder for product listing logic

def product_detail(request, product_id):
    pass  # Placeholder for product detail logic

def add_to_cart(request, product_id):
    pass  # Placeholder for add to cart logic


def view_cart(request):
    pass  # Placeholder for view cart logic


def checkout(request):
    pass  # Placeholder for checkout logic


def order_history(request):
    pass  # Placeholder for order history logic




def delete_product(request, product_id):
    pass  # Placeholder for delete product logic


def update_product(request, product_id):
    pass  # Placeholder for update product logic





def drivers(request):
    return render(request, 'drivers.html')


def diagnose(request):
    return render(request, 'diagnose.html')
