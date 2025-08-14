from django.urls import path
from .views import LogoutView, RegisterView, OTPVerifyView, LoginView, UserProfileView,UserInfoView, UserListView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('OtpVerify/', OTPVerifyView.as_view(), name='otp_verify'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', UserProfileView.as_view(), name='user_profile'),
    path('user-info/', UserInfoView.as_view(), name='user_profile'),
    path('user-list/', UserListView.as_view(), name='user_list')

]