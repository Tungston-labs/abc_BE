from rest_framework import serializers
from .models import User,OTP
from django.contrib.auth import get_user_model


class SuperAdminRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'phone', 'password', 'is_super_admin']
        read_only_fields = ['is_super_admin']

    def create(self, validated_data):
        validated_data['is_super_admin'] = True  # Force super admin
        return User.objects.create_user(**validated_data)



User = get_user_model()

class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField()

class OTPVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)

class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match")
        return data
