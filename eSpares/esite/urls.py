from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", views.login_view, name="login"),
    path("signup/", views.signup_view, name="signup"),
    path("logout/", views.logout_view, name="logout"),
    # path("profile/", views.profile_view, name="profile"),
    path('products/', views.product_list, name='product_list'),
    path('cart/', views.view_cart, name='cart'),
    path('products/<int:product_id>/', views.product_detail, name='product_detail'),
    path('products/<int:product_id>/add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('drivers/',views.drivers,name='drivers'),
    path('diagnose/',views.diagnose,name='diagnose'),
]
