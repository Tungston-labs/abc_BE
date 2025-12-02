from rest_framework import serializers
from .models import User,OTP
from django.contrib.auth import get_user_model

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        user = self.user

        # Safely get LCO name if exists
        lco_name = ''
        if hasattr(user, 'lco_profile') and user.lco_profile:
            lco_name = user.lco_profile.name

        data['user'] = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'phone': user.phone,
            'is_super_admin': user.is_super_admin,  # ✅ Add this
            'lco_name': lco_name,
        }

        return data
# from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
# from accounts.models import User



# class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):

#     def validate(self, attrs):

#         login_id = attrs.get("username")
#         password = attrs.get("password")

#         user = None

#         # Try email login
#         if User.objects.filter(email=login_id).exists():
#             user = User.objects.get(email=login_id)

#         # Try username login
#         elif User.objects.filter(username=login_id).exists():
#             user = User.objects.get(username=login_id)

#         else:
#             raise serializers.ValidationError({"detail": "Invalid username/email or password"})

#         # REQUIRED → because USERNAME_FIELD = "email"
#         attrs["email"] = user.email
#         attrs["username"] = user.email  # JWT uses this key, must be email value

#         # Now call normal JWT validation
#         data = super().validate(attrs)

#         user = self.user

#         # Optional: LCO profile
#         lco_name = getattr(getattr(user, "lco_profile", None), "name", "")

#         data["user"] = {
#             "id": user.id,
#             "username": user.username,
#             "email": user.email,
#             "phone": user.phone,
#             "is_super_admin": user.is_super_admin,
#             "lco_name": lco_name,
#         }

#         return data








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
