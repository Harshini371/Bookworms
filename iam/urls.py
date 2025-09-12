from django.urls import path
from .views import LogoutView, RegisterView, OTPVerifyView, LoginView, UserProfileView,UserInfoView, UserListView
from . import django_views as views

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('OtpVerify/', OTPVerifyView.as_view(), name='otp_verify'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', UserProfileView.as_view(), name='user_profile'),
    path('user-info/', UserInfoView.as_view(), name='user_profile'),
    path('user-list/', UserListView.as_view(), name='user_list'),
    path('register-view/', views.register_view, name='register'),
    path('verify-otp-view/', views.verify_otp_view, name='verify_otp_view'),
    path('login-view/', views.login_view, name='login_view'),
    path('logout-view/', views.logout_view, name='logout_view'),
    path('profile-view/', views.profile_view, name='profile-view'),
    path('home-view/', views.home_view, name="home-view"),
    path('authors-view/', views.authors_view, name="authors-view"),
    path('vendors-view/', views.vendors_view, name ="vendors-view")

]

