from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", views.login_view, name="login"),
    path("signup/", views.signup_view, name="signup"),
    path("logout/", views.logout_view, name="logout"),
    path('products/', views.product_list, name='product_list'),
    path('cart/', views.view_cart, name='cart'),
    path('products/<int:product_id>/', views.product_detail, name='product_detail'),
    path('products/<int:product_id>/add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('drivers/',views.drivers,name='drivers'),
    path('diagnose/',views.diagnose,name='diagnose'),
    path('account/', views.profile_view, name='profile'),
    path('devices/', views.device_list, name='device_list'),
    path('devices/add/', views.device_add, name='device_add'),
    path('devices/<int:device_id>/photo/', views.device_photo, name='device_photo'),
    path('repairs/book/', views.repair_booking, name='repair_booking'),
    path('repairs/', views.repair_list, name='repair_list'),
    path('repairs/track/', views.repair_tracking, name='repair_tracking'),
    path('repairs/<str:reference>/invoice/<str:invoice_number>/', views.repair_invoice, name='repair_invoice'),
    path('repairs/<str:reference>/photos/<int:photo_id>/', views.repair_photo, name='repair_photo'),
    path('repairs/<str:reference>/', views.repair_detail, name='repair_detail'),
    path('contact/', views.contact_view, name='contact'),
    path('support/chat/', views.support_chat, name='support_chat'),
    path('support/chat/<int:conversation_id>/', views.support_chat_thread, name='support_chat_thread'),
    path('support/chat/<int:conversation_id>/messages/', views.support_chat_messages, name='support_chat_messages'),
]
