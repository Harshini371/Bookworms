from rest_framework import serializers
from .models import CustomUser, profile
import logging

logger = logging.getLogger(__name__)



class CustomUserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(required=True, max_length=30)
    last_name = serializers.CharField(required=True, max_length=30)
    Otp = serializers.CharField( required=False)
    username = serializers.CharField(required=True, max_length=30)
    Otp_expiry = serializers.DateTimeField( required=False)
    user_type = serializers.ChoiceField(choices=[
        ('admin', 'Admin'),
        ('customer', 'Customer'),
        ('vendor', 'Vendor'),
        ('delivery', 'Delivery'),
        ('superadmin', 'SuperAdmin'),
    ], default='customer')

    class Meta:
        model = CustomUser
        fields = ['id','email' ,'password', 'first_name', 'last_name', 'Otp','Otp_expiry', 'username','user_type']
    
    def validate_email(self, value):
        if CustomUser.objects.filter(email=value, is_active=True).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = CustomUser(**validated_data)
        user.set_password(password)
        user.is_active = False  # User is inactive until OTP verification
        user.save()
        return user
    
class OTPVerifyRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
    Otp = serializers.CharField()
    Otp_expiry = serializers.DateTimeField(required=False)

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)

class UserProfileSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    D_no = serializers.CharField(max_length=255, required=False)
    street_name = serializers.CharField(max_length=255, required=False)
    city = serializers.CharField(max_length=100, required=False)
    state = serializers.CharField(max_length=100, required=False)
    country = serializers.CharField(max_length=100, required=False)
    zip_code = serializers.CharField(max_length=20, required=False)
    phone_number = serializers.CharField(max_length=15, required=False)

    class Meta:
        model = profile
        fields = ['user', 'D_no', 'street_name', 'city', 'state', 'country', 'zip_code', 'phone_number']

    def create(self, validated_data):
        user = self.context['request'].user
        profile_data = validated_data.copy()
        profile_data['user'] = user
        profile_instance = profile.objects.create(**profile_data)
        return profile_instance

   

    



