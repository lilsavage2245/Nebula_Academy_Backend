# core/serializers
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.contrib.auth.tokens import default_token_generator
from django.db import transaction
from django.contrib.auth.password_validation import validate_password
from core.utils.email import send_verification_email, send_password_reset_email, send_password_changed_notification
from core.signals import user_registered
from core.models import UserActivityLog
from django.utils import timezone
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from program.models import ProgramLevel, ProgramCategory

from core.utils.request import get_client_ip

import logging

logger = logging.getLogger(__name__)

UserModel = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for existing users; read-only fields include slug and date_joined.
    """
    class Meta:
        model = UserModel
        fields = [
            'id',
            'email',
            'first_name',
            'last_name',
            'slug',
            'role',
            'school_email_verified',
            'is_active',
            'date_joined',
        ]
        read_only_fields = ['id', 'slug', 'school_email_verified', 'is_active', 'date_joined', 'role']

        def update(self, instance, validated_data):
            # Only allow role change if context user is admin
            request = self.context.get('request')
            if 'role' in self.initial_data:
                if not (request and request.user.is_superuser):
                    raise serializers.ValidationError({'role': 'You do not have permission to change roles.'})
                instance.role = validated_data.get('role', instance.role)
            # Update other fields
            instance.first_name = validated_data.get('first_name', instance.first_name)
            instance.last_name = validated_data.get('last_name', instance.last_name)
            instance.save()
            return instance


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    # allow these on create
    program_level = serializers.PrimaryKeyRelatedField(
        queryset=ProgramLevel.objects.select_related('program').all(),
        required=False,
        allow_null=True
    )
    program_category = serializers.ChoiceField(
        choices=ProgramCategory.choices,
        required=False,
        allow_null=True
    )

    class Meta:
        model = UserModel
        fields = ['email', 'first_name', 'last_name', 'password', 'role', 'program_level', 'program_category']

    def validate(self, attrs):
        role = attrs.get('role')
        program_level = attrs.get('program_level')
        program_category = attrs.get('program_category')

        errors = {}
        if role == UserModel.Roles.ENROLLED:
            if not program_level:
                errors['program_level'] = 'Enrolled students must have a Program Level (e.g., Beginner Level 1).'
        if role == UserModel.Roles.FREE:
            if not program_category:
                errors['program_category'] = 'Free students must have a Program Category (e.g., BEG for Beginner).'

        if errors:
            raise serializers.ValidationError(errors)
        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password')

        # If ENROLLED and level provided, mirror the category into program_category
        role = validated_data.get('role')
        level = validated_data.get('program_level')
        if role == UserModel.Roles.ENROLLED and level:
            validated_data['program_category'] = level.program.category

        user = UserModel.objects.create_user(password=password, **validated_data)
        return user

class ResendVerificationSerializer(serializers.Serializer):
    """
    Serializer for resending the email verification link to users who haven’t yet verified.
    Always returns success to avoid revealing whether the email exists or is verified.
    """
    email = serializers.EmailField()

    def save(self, **kwargs):
        request = self.context.get('request')
        # Try sending a verification email if user exists and is not verified
        try:
            user = UserModel.objects.get(email=self.validated_data.get('email'))
            if not (user.is_active and user.school_email_verified):
                send_verification_email(user, request)
        except UserModel.DoesNotExist:
            pass
        return {}


class EmailVerificationSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()

    def save(self, **kwargs):
        """
        Secure email verification.

        - Swallows all errors to prevent user enumeration or timing attacks.
        - Uses atomic transaction for DB safety.
        - Logs any internal failure for dev ops visibility.
        - Returns generic success message either way.
        """
        try:
            uid_str = force_str(urlsafe_base64_decode(self.validated_data['uid']))
            user = get_user_model().objects.get(pk=uid_str)

            if default_token_generator.check_token(user, self.validated_data['token']):
                with transaction.atomic():
                    user.is_active = True
                    user.school_email_verified = True
                    user.save(update_fields=['is_active', 'school_email_verified'])
        except Exception as e:
            logger.warning("Email verification failed", exc_info=True)

        return {
            "detail": "If the link was valid, your account has been verified."
        }


class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login.
    """
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        from django.contrib.auth import authenticate

        user = authenticate(
            email=attrs.get('email'),
            password=attrs.get('password')
        )
        if not user:
            raise serializers.ValidationError("Invalid email or password.")
        if not user.is_active:
            raise serializers.ValidationError("Account is not active.")
        attrs['user'] = user
        return attrs

class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Serializer for requesting a password reset email.
    Always returns success to prevent revealing account existence.
    """
    email = serializers.EmailField()

    def save(self, **kwargs):
        request = self.context.get('request')
        try:
            user = UserModel.objects.get(email=self.validated_data.get('email'))
            if user.is_active:
                send_password_reset_email(user, request)
        except UserModel.DoesNotExist:
            pass
        return {}

class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        validate_password(data['new_password'])  # Enforce Django password rules
        return data

    def save(self, **kwargs):
        request = self.context.get('request')

        try:
            uid = force_str(urlsafe_base64_decode(self.validated_data['uid']))
            user = get_user_model().objects.get(pk=uid)

            if default_token_generator.check_token(user, self.validated_data['token']):
                with transaction.atomic():
                    user.set_password(self.validated_data['new_password'])
                    user.password_changed_at = timezone.now()
                    user.save(update_fields=['password', 'password_changed_at'])

                if request:
                    # Send confirmation email
                    send_password_changed_notification(user, request=request)

                    # Log user activity
                    UserActivityLog.objects.create(
                        user=user,
                        action="Password Reset",
                        ip_address=get_client_ip(request),
                        user_agent=request.META.get("HTTP_USER_AGENT"),
                        device_type=request.META.get("HTTP_USER_AGENT")
                    )
        except Exception as e:
            logger.warning("Password reset failed", exc_info=True)

        return {
            "detail": "If the link was valid, your password has been reset."
        }