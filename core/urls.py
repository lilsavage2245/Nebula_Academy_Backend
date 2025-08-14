# core/urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    RegisterAPIView,
    VerifyEmailAPIView,
    UserDetailAPIView,
    ResendVerificationAPIView,
    PasswordResetRequestAPIView,
    PasswordResetConfirmAPIView,
)

urlpatterns = [
    # --- Auth (JWT) ---
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # (Optional) Back-compat alias: keep /login/ pointing to JWT
    path("login/", TokenObtainPairView.as_view(), name="token_login_alias"),

    # --- User / profile ---
    path("me/", UserDetailAPIView.as_view(), name="user-detail"),

    # --- Registration & verification ---
    path("register/", RegisterAPIView.as_view(), name="register"),
    path("verify-email/", VerifyEmailAPIView.as_view(), name="verify-email"),
    path("resend-verification/", ResendVerificationAPIView.as_view(), name="resend-verification"),

    # --- Password reset ---
    path("password-reset/", PasswordResetRequestAPIView.as_view(), name="password-reset-request"),
    path("password-reset-confirm/", PasswordResetConfirmAPIView.as_view(), name="password-reset-confirm"),
]

