# core/models.py
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone
from common.mixins import SlugModelMixin
from django.conf import settings
from django.db.models import Q


class ProgramCategory(models.TextChoices):
    PRE = "PRE", "Pre-Academy"
    BEG = "BEG", "Beginner"
    INT = "INT", "Intermediate"
    ADV = "ADV", "Advanced"


class UserManager(BaseUserManager):
    def create_user(self, email, first_name, last_name, password=None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            first_name=first_name,
            last_name=last_name,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, first_name, last_name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        # Superuser is effectively an administrator
        extra_fields.setdefault('role', User.Roles.ADMIN)
        return self.create_user(email, first_name, last_name, password, **extra_fields)

class User(SlugModelMixin, AbstractBaseUser, PermissionsMixin):
    from program.models import ProgramCategory
    class Roles(models.TextChoices):
        ENROLLED  = 'ENROLLED',  'Enrolled Student'
        FREE      = 'FREE',      'Free Student'
        LECTURER  = 'LECTURER',  'Lecturer'
        VOLUNTEER = 'VOLUNTEER', 'Volunteer'
        BLOGGER   = 'BLOGGER',   'News Blogger'
        PARTNER   = 'PARTNER',   'Partner'
        ADMIN     = 'ADMIN',     'Administrator'

    slug_source_field = 'slug_source'
    slug_max_length = 100

    email                    = models.EmailField(unique=True)
    first_name               = models.CharField(max_length=100)
    last_name                = models.CharField(max_length=100)
    slug                     = models.SlugField(unique=True, blank=True)
    role                     = models.CharField(max_length=20, choices=Roles.choices)
    program_level = models.ForeignKey(
        'program.ProgramLevel',            # string ref avoids import-cycle headaches
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='students'
    )
    #program_category = models.CharField(
    #    max_length=3,
    #    choices=ProgramCategory.choices,
    #    null=True, blank=True,
    #    help_text="Required for FREE users; for ENROLLED users this mirrors the level's program category."
    #)

    program_category = models.CharField(
        max_length=3,
        choices=ProgramCategory.choices,
        null=True, blank=True,
        help_text="Required for FREE users; mirrors program level for ENROLLED users."
    )

    school_email_verified    = models.BooleanField(default=False)

    # Forward‑thinking fields
    mfa_enabled           = models.BooleanField(default=False, help_text='Whether multi‑factor authentication is enabled')
    social_auth_provider  = models.CharField(max_length=32, null=True, blank=True, help_text='Provider name for social login')
    is_deleted            = models.BooleanField(default=False, help_text='Soft‑delete flag for GDPR compliance')
    deleted_at            = models.DateTimeField(null=True, blank=True, help_text='Timestamp when user was soft‑deleted')

    profile_picture = models.ImageField(
        upload_to='profile_pics/',
        blank=True,
        null=True,
        help_text="User avatar/profile image"
    )

    location = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        help_text="City and country, e.g., 'Leeds, United Kingdom'"
    )

    # Optional: only if you want theme/filter global to User instead of just Free Dashboard
    theme_preference = models.CharField(
        max_length=20,
        choices=[('LIGHT', 'Light'), ('DARK', 'Dark')],
        blank=True,
        null=True,
        help_text="Optional theme preference (can override dashboard)"
    )

    personalised_class_filter = models.CharField(
        max_length=20,
        choices=[
            ('ALL', 'All Classes'),
            ('NEBULA_ONLY', 'Only Nebula Lecturers'),
            ('GUEST_ONLY', 'Only Guest Facilitators')
        ],
        blank=True,
        null=True,
        help_text="Default class filter preference"
    )

    # System flags
    is_active                = models.BooleanField(default=False)
    is_staff                 = models.BooleanField(default=False)
    date_joined              = models.DateTimeField(default=timezone.now)
    password_changed_at = models.DateTimeField(null=True, blank=True,
        help_text='Timestamp when password was last reset or changed.')

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'role']

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        return self.first_name

    @property
    def slug_source(self):
        return self.email.split('@')[0] if self.email else f"{self.first_name}-{self.last_name}"

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"
    
    class Meta:
        ordering = ['-date_joined']
        constraints = [
            # If ENROLLED => program_level required
            models.CheckConstraint(
                name="enrolled_requires_program_level",
                check=Q(role='ENROLLED', program_level__isnull=False) | ~Q(role='ENROLLED'),
            ),
            # If FREE => program_category required
            models.CheckConstraint(
                name="free_requires_program_category",
                check=Q(role='FREE', program_category__isnull=False) | ~Q(role='FREE'),
            ),
        ]

class UserActivityLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='activity_logs')
    action = models.CharField(max_length=255)  # e.g. "Password Reset"
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    user_agent = models.CharField(max_length=256, null=True, blank=True,
        help_text='User agent string during the action.')
    device_type = models.CharField(max_length=64, null=True, blank=True,
        help_text='Parsed device type (mobile, desktop, etc.).')

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user.email} - {self.action} at {self.timestamp}"
