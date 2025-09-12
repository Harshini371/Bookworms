from django.shortcuts import render
from django.http import JsonResponse
from django.views import View
from django.contrib.auth import get_user_model

from .models import CustomUser, profile

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .serializer import CustomUserSerializer, OTPVerifyRequestSerializer, LoginSerializer, UserProfileSerializer
from django.conf import settings
from datetime import timedelta
import random
from django.utils import timezone
from django.core.mail import send_mail
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import logging
logger = logging.getLogger(__name__)
from django.contrib.auth import authenticate
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from .permissions import IsAdminUser, IsCustomerUser, IsVendorUser, IsDeliveryUser, IsSuperAdminUser




# Create your views here.

def generate_otp():
    return str(random.randint(100000, 999999))


class RegisterView(APIView):
    
    def post(self, request, *args, **kwargs):

        try:
            email = request.data.get('email')
            if not email:
                return Response({"error": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)
            current_user = CustomUser.objects.get(email=email)
            if current_user.is_active:
                return Response({"error": "User already exists."}, status=status.HTTP_400_BAD_REQUEST)
            elif not current_user.is_active:
                logger.debug("User {email} is not active, But user exists, proceeding with registration, sending OTP again.") 

                otp = generate_otp()
                current_user.Otp = otp
                current_user.Otp_expiry = timezone.now() + timedelta(minutes=5)
                current_user.username = request.data.get('username')
                current_user.set_password(request.data.get('password'))
                current_user.first_name = request.data.get('first_name')
                current_user.last_name = request.data.get('last_name')
                current_user.user_type = request.data.get('user_type', 'customer')  # Default to 'customer' if not provided
                current_user.save()

                send_mail(
                    'Your OTP Code',
                    f'Your OTP code is {current_user.Otp}. It is valid for 5 minutes.',
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )
                logger.info(f"OTP {current_user.Otp} sent to {email}")
                return Response({"message": "Current user {email} already exists, For Verification, OTP sent Successfully."}, status=status.HTTP_200_OK)
            
        except CustomUser.DoesNotExist:
            try:
                otp = generate_otp()
                request.data['Otp'] = otp
                logger.debug(f"Creating new user with email {request.data['email']} and OTP {request.data['Otp']}")
                request.data['Otp_expiry'] = timezone.now() + timedelta(minutes=5)
                serializer = CustomUserSerializer(data=request.data)
                if serializer.is_valid():
                    logger.debug(f"Serializer is valid for user {serializer.validated_data}")
                    current_user = serializer.save()
                    
                    send_mail(
                        'Your OTP Code',
                        f'Your OTP code is {serializer.data["Otp"]}. It is valid for 5 minutes.',   
                        settings.DEFAULT_FROM_EMAIL,
                        [serializer.data['email']],
                        fail_silently=False,
                    )
                    logger.info(f"OTP {serializer.data['Otp']} sent to {serializer.data['email']}")
                    return Response(serializer.data, status=status.HTTP_201_CREATED)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
            except Exception as e:
                logger.error(f"Error during registration: {str(e)}")
                return Response({"error": "An error occurred during registration."+ str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

class OTPVerifyView(APIView):
    
    def post(self, request, *args, **kwargs):
        try:
            request.data['Otp_expiry'] = timezone.now() + timedelta(minutes=5)
            serialiser = OTPVerifyRequestSerializer(data=request.data)
            if serialiser.is_valid():
                email = request.data['email']
                Otp = request.data['Otp']
                
                try:
                    current_user = CustomUser.objects.get(email=email, Otp=Otp, Otp_expiry__gte=timezone.now())
                    current_user.is_active = True
                    current_user.Otp = None
                    current_user.Otp_expiry = None
                    current_user.save()
                    logger.info(f"OTP {Otp} verified for user {email}")
                    return Response({"message": "OTP verified successfully."}, status=status.HTTP_200_OK)
                
                except CustomUser.DoesNotExist:
                    logger.warning(f"OTP verification failed for user {email}. Invalid OTP or expired.")
                    return Response({"error": "Invalid OTP or OTP has expired."}, status=status.HTTP_400_BAD_REQUEST)
            
            return Response(serialiser.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Error during OTP verification: {str(e)}")
            return Response({"error": "An error occurred during OTP verification." + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class LoginView(APIView):
    def post(self, request, *args, **kwargs):
        try:
            serializer = LoginSerializer(data=request.data)
            if serializer.is_valid():
                email = serializer.validated_data['email']
                password = serializer.validated_data['password']
                user = authenticate(email=email, password=password)
                if user is not None and user.is_active:
                    refresh = RefreshToken.for_user(user)
                    logger.info(f"User {email} logged in successfully.")
                    payload_data = {
                            'email' : user.email,
                            'userName' : user.username,
                            'full_name' : ' '.join([user.first_name, user.last_name]).strip() if user.first_name or user.last_name else '',
                            'user_id' : user.id
                    }
                    refresh.payload.update(payload_data)
                    return Response({
                        'data':{
                        'refresh': str(refresh),
                        'access': str(refresh.access_token), 
                        'user_data' : payload_data,
                        'message':'logged in successfully'}},status=status.HTTP_200_OK)
                else:
                    logger.warning(f"Login failed for user {email}. User not found or inactive.")
                    return Response({"error": "Invalid credentials or user is inactive."}, status=status.HTTP_400_BAD_REQUEST)
                
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error during login: {str(e)}")
            return Response({"error": "An error occurred during login." + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                



class LogoutView(APIView):
    permission_classes = [IsAuthenticated]  # Ensures user is authenticated before logout

    def post(self, request, *args, **kwargs):
        # Get the Authorization header
        auth_header = request.headers.get('Authorization')

        if not auth_header or not auth_header.startswith('Bearer '):
            return Response({"error": "Authorization header with Bearer token required."},
                            status=status.HTTP_400_BAD_REQUEST)

        access_token = auth_header.split(' ')[1]  # Extract token string
        logger.info(f"User {request.user.email} is attempting to log out with token: {access_token}")
        try:
            # If you only have the access token, you cannot directly blacklist it.
            # Normally, the refresh token must be sent for blacklisting.
            # But if you have JWT settings to allow blacklisting of access tokens:
            refresh_token = request.data.get('refresh')  # Optional, if you want to blacklist refresh token as well
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            else:
                return Response({"error": "Refresh token is required for logout."},
                                status=status.HTTP_400_BAD_REQUEST)

            logger.info("User logged out successfully. Token blacklisted.")
            return Response({"message": "Logged out successfully."}, status=status.HTTP_200_OK)

        except TokenError:
            logger.warning("Invalid or expired token provided for logout.")
            return Response({"error": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Error during logout: {str(e)}")
            return Response({"error": "An error occurred during logout."},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):
        try:
            user = request.user
            current_user = CustomUser.objects.get(email=user.email)
            user_data = {
                'id': current_user.id,
                'email':current_user.email,
                'first_name': current_user.first_name,
                'last_name': current_user.last_name,
                'username': current_user.username,
                'user_type': current_user.user_type}
            return Response(user_data, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            logger.error(f"User with email {request.user.email} does not exist.")
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error retrieving user profile: {str(e)}")
            return Response({"error": "An error occurred while retrieving the user profile." + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def put(self, request, *args, **kwargs):
        try:
            user = request.user
            current_user = CustomUser.objects.get(email=user.email)
            for key,value in request.data.items():
                if key == "first_name":
                    current_user.first_name = value
                elif key == "last_name":
                    current_user.last_name = value
                elif key == "user_type":
                    current_user.user_type = value
                elif key == "password":
                    current_user.set_password(value)
                else:
                    return Response({"error": f"Invalid field: {key}"}, status=status.HTTP_400_BAD_REQUEST)
            current_user.save()
            user_data = {
                'id': current_user.id,
                'email': current_user.email,
                'first_name': current_user.first_name,
                'last_name': current_user.last_name,
                'user_type': current_user.user_type      
            }
            logger.info(f"User profile updated for {user.email}.")
            return Response(user_data, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            logger.error(f"User with email {user.email} does not exist.")
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error updating user profile: {str(e)}")
            return Response({"error": "An error occurred while updating the user profile." + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def delete(self, request, *args, **kwargs):
        try:
            user = request.user
            current_user = CustomUser.objects.get(email=user.email)
            current_user.is_active = False
            current_user.save()
            logger.info(f"User {user.email} has been deactivated.")
            return Response({"message": "User account deactivated successfully."}, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            logger.error(f"User with email {user.email} does not exist.")
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error deactivating user account: {str(e)}")
            return Response({"error": "An error occurred while deactivating the user account." + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class UserInfoView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, *args, **kwargs):
        try:
            user = request.user
            logger.debug(f"Creating profile for user {user} with data: {request.data}")
            profile_data = request.data
            profile_data['user'] = user
            logger.debug(f"Creating profile for user {user.email} with data: {profile_data}")
            serializer = UserProfileSerializer(data=profile_data, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                logger.info(f"Profile created for user {user.email}.")
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error creating user profile: {str(e)}")
            return Response({"error": "An error occurred while creating the user profile." + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def get(self, request, *args, **kwargs):
        try:
            user = request.user
            profile_obj = profile.objects.get(user=user)
            profile_data = {
                'D_no': profile_obj.D_no,
                'street_name': profile_obj.street_name, 
                'city': profile_obj.city,
                'state': profile_obj.state,
                'country': profile_obj.country, 
                'zip_code': profile_obj.zip_code,
                'phone_number': profile_obj.phone_number
            }
            logger.info(f"Profile retrieved for user {user.email}.")
            return Response(profile_data, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Error retrieving user profile: {str(e)}")
            return Response({"error": "An error occurred while retrieving the user profile." + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def put(self, request, *args, **kwargs):
        try: 
            user = request.user
            profile_obj = profile.objects.get(user=user)
            for key, value in request.data.items():
                if hasattr(profile_obj, key):
                    setattr(profile_obj, key, value)
            profile_obj.save()
            profile_data = {
                'D_no': profile_obj.D_no,
                'street_name': profile_obj.street_name,
                'city': profile_obj.city,
                'state': profile_obj.state,
                'country': profile_obj.country,
                'zip_code': profile_obj.zip_code,
                'phone_number': profile_obj.phone_number
            }
            logger.info(f"Profile updated for user {user.email}.")
            return Response(profile_data, status=status.HTTP_200_OK)
        except profile.DoesNotExist:
            logger.error(f"Profile for user {user.email} does not exist.")
            return Response({"error": "Profile not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error updating user profile: {str(e)}")
            return Response({"error": "An error occurred while updating the user profile." + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class UserListView(APIView):
    permission_classes = [IsAdminUser]
    def get(self, request, *args, **kwargs):
        try:
            if request.user.user_type == 'admin':
                users = CustomUser.objects.all()
                user_data = []
                for user in users:
                    user_data.append({
                        'id': user.id,
                        'email': user.email,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'username': user.username,
                        'user_type': user.user_type,
                        'is_active': user.is_active,
                        'date_joined': user.date_joined
                    })
                    logger.debug(f"User data for {user.email}: {user_data[-1]}")
                logger.info("User list retrieved successfully.")
                return Response(user_data, status=status.HTTP_200_OK)
            return Response({"error": "You do not have permission to view this resource."}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            logger.error(f"Error retrieving user list: {str(e)}")
            return Response({"error": "An error occurred while retrieving the user list." + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)