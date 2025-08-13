# core/urls.py
from django.urls import path
from .views import RegisterAPIView, VerifyEmailAPIView, LoginAPIView, UserDetailAPIView, ResendVerificationAPIView, PasswordResetRequestAPIView, PasswordResetConfirmAPIView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', RegisterAPIView.as_view(), name='register'),
    path('verify-email/', VerifyEmailAPIView.as_view(), name='verify-email'),
    path('resend-verification/', ResendVerificationAPIView.as_view(), name='resend-verification'),
    path('login/', LoginAPIView.as_view(), name='login'),
    path('me/', UserDetailAPIView.as_view(), name='user-detail'),
    path('password-reset/', PasswordResetRequestAPIView.as_view(), name='password-reset-request'),
    path('password-reset-confirm/', PasswordResetConfirmAPIView.as_view(), name='password-reset-confirm'),


]
