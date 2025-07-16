from django.urls import path
from accounts import views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('register-superadmin/',views.SuperAdminRegisterView.as_view(), name='register-superadmin'),

        # Login (obtain access + refresh tokens)
    path('login/',TokenObtainPairView.as_view(), name='token_obtain_pair'),

    # Refresh access token
    path('token/refresh/',TokenRefreshView.as_view(), name='token_refresh'),

    # Logout
    path('logout/',views.LogoutView.as_view(), name='logout'),

    path('forgot-password/send-otp/', views.SendOTPView.as_view(), name='send-otp'),
    path('forgot-password/verify-otp/', views.VerifyOTPView.as_view(), name='verify-otp'),
    path('forgot-password/reset-password/', views.ResetPasswordView.as_view(), name='reset-password'),


    # CHANGE PASSWORD

    path('change-password/', views.ChangePasswordView.as_view(), name='change-password'),

]
