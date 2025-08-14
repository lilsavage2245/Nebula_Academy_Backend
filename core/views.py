# core/views.py
from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth.tokens import default_token_generator

from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token

from .serializers import (
    RegisterSerializer,
    EmailVerificationSerializer,
    LoginSerializer,
    UserSerializer,
    ResendVerificationSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
)
from core.serializers import UserSerializer  # make sure you have this

from rest_framework import mixins, viewsets, permissions

from .throttling import PasswordResetRateThrottle

User = get_user_model()

class UserViewSet(mixins.RetrieveModelMixin,
                  mixins.ListModelMixin,
                  viewsets.GenericViewSet):
    """
    Read-only User ViewSet — required for nested routers
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]  # or IsAuthenticated
    lookup_field = 'id'  # match your lookup='user' in router

class RegisterAPIView(generics.CreateAPIView):
    """
    Handles user registration. Sends a verification email upon successful signup.
    """
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {"detail": "Registration successful. Please check your email to verify your account."},
            status=status.HTTP_201_CREATED
        )


class VerifyEmailAPIView(APIView):
    """
    Secure endpoint for verifying user email via uid/token query params.
    Always returns generic success or failure.
    """
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        # Accept uid/token as query params
        serializer = EmailVerificationSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        # Delegate to secure serializer logic
        serializer.save()

        return Response(
            {"detail": "If the link was valid, your account has been verified."},
            status=status.HTTP_200_OK
        )

class ResendVerificationAPIView(APIView):
    """
    Allows users to request a new email verification link.
    """
    permission_classes = [AllowAny]
    serializer_class = ResendVerificationSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "Verification email resent."},
            status=status.HTTP_200_OK
        )

class LoginAPIView(APIView):
    """
    Authenticates user credentials and returns an auth token.
    """
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        token, _ = Token.objects.get_or_create(user=user)
        return Response(
            {"token": token.key},
            status=status.HTTP_200_OK
        )


class UserDetailAPIView(generics.RetrieveAPIView):
    """
    Retrieves current authenticated user's details.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

class PasswordResetRequestAPIView(APIView):
    """
    Handles password reset requests by sending a reset link.
    Always returns success to prevent information leakage.
    Request password reset link. Throttled to 3 requests per hour per email.
    """
    permission_classes = [AllowAny]
    serializer_class = PasswordResetRequestSerializer
    throttle_classes = [PasswordResetRateThrottle]

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "If the email exists, a password reset link has been sent."},
            status=status.HTTP_200_OK
        )

class PasswordResetConfirmAPIView(APIView):
    """
    Confirms password reset using UID and token and sets a new password.
    Always returns success to prevent information leakage.
    """
    permission_classes = [AllowAny]
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        return Response(result, status=status.HTTP_200_OK)

# --- Me (whoami) + Logout (token-based) ---
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

class MeAPIView(APIView):
    """
    Return the current authenticated user's profile.
    Token required: Authorization: Token <key>
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        u = request.user
        data = {
            "id": u.id,
            "email": getattr(u, "email", ""),
            "username": u.get_username(),
            "first_name": getattr(u, "first_name", ""),
            "last_name": getattr(u, "last_name", ""),
            "is_staff": u.is_staff,
            "is_superuser": u.is_superuser,
        }
        return Response(data, status=status.HTTP_200_OK)


class LogoutAPIView(APIView):
    """
    Invalidate the current token by deleting it (server-side logout).
    Note: This style logs out only the token used in this request.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # delete the token presented in the Authorization header
        try:
            Token.objects.get(user=request.user, key=request.auth.key).delete()
        except Exception:
            # fall back: delete ALL tokens for the user (optional)
            # Token.objects.filter(user=request.user).delete()
            pass
        return Response({"ok": True}, status=status.HTTP_200_OK)
