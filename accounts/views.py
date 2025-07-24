from django.shortcuts import render

from rest_framework import generics
from rest_framework.permissions import AllowAny
from .serializers import SuperAdminRegisterSerializer
from .models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework import status
from .models import OTP
from django.contrib.auth import get_user_model
from .serializers import EmailSerializer, OTPVerifySerializer, PasswordResetSerializer
from django.core.mail import send_mail
import random
from django.conf import settings

class SuperAdminRegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = SuperAdminRegisterSerializer
    permission_classes = [AllowAny]  


    
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


# logout view

class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"detail": "Logout successful."}, status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({"error": "Invalid refresh token."}, status=status.HTTP_400_BAD_REQUEST)



# forgot password 



User = get_user_model()

class SendOTPView(APIView):
    permission_classes = [AllowAny]  


    def post(self, request):
        serializer = EmailSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response({"error": "Email not found"}, status=status.HTTP_404_NOT_FOUND)

            otp = str(random.randint(100000, 999999))
            OTP.objects.create(user=user, otp=otp)

            # Send OTP via email (setup EMAIL_BACKEND in settings)
            send_mail(
                subject="Your OTP Code",
                message=f"Your OTP is: {otp}",
                from_email= settings.EMAIL_HOST_USER,

                recipient_list=[email],
            )

            return Response({"message": "OTP sent successfully"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VerifyOTPView(APIView):
    permission_classes = [AllowAny]  

    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            otp_input = serializer.validated_data['otp']
            try:
                user = User.objects.get(email=email)
                otp_obj = OTP.objects.filter(user=user, otp=otp_input, is_verified=False).last()

                if not otp_obj:
                    return Response({"error": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)
                if otp_obj.is_expired():
                    return Response({"error": "OTP expired"}, status=status.HTTP_400_BAD_REQUEST)

                otp_obj.is_verified = True
                otp_obj.save()
                return Response({"message": "OTP verified"}, status=status.HTTP_200_OK)

            except User.DoesNotExist:
                return Response({"error": "Email not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ResetPasswordView(APIView):
    permission_classes = [AllowAny]  

    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            new_password = serializer.validated_data['new_password']

            try:
                user = User.objects.get(email=email)
                otp_obj = OTP.objects.filter(user=user, is_verified=True).last()

                if not otp_obj:
                    return Response({"error": "OTP not verified"}, status=status.HTTP_400_BAD_REQUEST)

                user.set_password(new_password)
                user.save()

                otp_obj.delete()  # Invalidate used OTP
                return Response({"message": "Password reset successful"}, status=status.HTTP_200_OK)

            except User.DoesNotExist:
                return Response({"error": "Email not found"}, status=status.HTTP_404_NOT_FOUND)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




# CHANGE PASSWORD


from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')

        if not user.check_password(old_password):
            return Response({'error': 'Old password is incorrect.'}, status=status.HTTP_400_BAD_REQUEST)

        if new_password != confirm_password:
            return Response({'error': 'New password and confirm password do not match.'}, status=status.HTTP_400_BAD_REQUEST)

        if old_password == new_password:
            return Response({'error': 'New password must be different from the old password.'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        return Response({'message': 'Password changed successfully.'}, status=status.HTTP_200_OK)
