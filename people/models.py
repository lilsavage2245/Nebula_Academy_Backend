# people/models.py
from django.db import models
from django.conf import settings
from common.mixins import SlugModelMixin
from django.urls import reverse


class BaseProfile(SlugModelMixin, models.Model):
    slug_source_field = 'slug_source'
    slug_max_length = 150
    """
    Abstract base for additional user profile information.
    """
    bio = models.TextField(blank=True)
    profile_image = models.ImageField(
        upload_to='profiles/', null=True, blank=True,
        help_text='Optional avatar or profile photo'
    )
    website = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)
    twitter = models.URLField(blank=True)
    github = models.URLField(blank=True)

    # Optional search optimization tags
    tags = models.JSONField(
        blank=True,
        null=True,
        help_text='Optional list of keywords for frontend filtering/search'
    )

        # Admin verification fields
    is_verified = models.BooleanField(default=False, help_text="Admin approval status")
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="approved_%(class)s_profiles"
    )
    approved_on = models.DateTimeField(null=True, blank=True)

    slug = models.SlugField(max_length=150, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    @property
    def slug_source(self):
        try:
            return self.user.get_full_name()
        except Exception:
            return "unknown-user"


class Expertise(SlugModelMixin, models.Model):
    slug_source_field = 'name'
    slug_max_length = 100
    """
    Tags or areas of expertise for lecturers.
    """
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)

    def __str__(self):
        return self.name


# Lecturer Profile
class LecturerProfile(BaseProfile):
    """
    Extended profile for users with role=LECTURER.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='lecturer_profile',
        limit_choices_to={'role': 'LECTURER'}
    )
    expertise = models.ManyToManyField(
        Expertise,
        blank=True,
        related_name='lecturers',
        help_text='Areas of expertise or teaching subjects'
    )
    qualifications = models.TextField(blank=True)
    office_hours = models.JSONField(
        blank=True,
        null=True,
        help_text='Example: {"Monday": ["10:00-12:00"], "Wednesday": ["14:00-16:00"]}'
    )

    def get_absolute_url(self):
        return reverse("lecturer-profile", kwargs={"slug": self.slug})

    def __str__(self):
        return f"Lecturer Profile: {self.user.get_full_name()}"


# Director Profile
class ProgramDirectorProfile(BaseProfile):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='director_profile',
        limit_choices_to={'role': 'ADMIN'}
    )
    department = models.CharField(max_length=100, blank=True)
    office_hours = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"Director: {self.user.get_full_name()}"
    

# volunteer Profile
class VolunteerProfile(BaseProfile):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='volunteer_profile',
        limit_choices_to={'role': 'VOLUNTEER'}
    )
    interests = models.JSONField(
        blank=True, null=True,
        help_text='e.g. ["Event Support", "Mentorship", "Logistics"]'
    )
    availability = models.JSONField(
        blank=True, null=True,
        help_text='e.g. {"Weekdays": ["Morning"], "Weekends": ["Afternoon"]}'
    )

    def __str__(self):
        return f"Volunteer: {self.user.get_full_name()}"


# Blogger/content writer Profile
class BloggerProfile(BaseProfile):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='blogger_profile',
        limit_choices_to={'role': 'BLOGGER'}
    )
    pen_name = models.CharField(max_length=100, blank=True, help_text='Optional pen name')

    @property
    def slug_source(self):
        return self.pen_name or self.user.get_full_name()


    def __str__(self):
        return f"Blogger: {self.pen_name or self.user.get_full_name()}"


# Partner Profile
class PartnerProfile(BaseProfile):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='partner_profile',
        limit_choices_to={'role': 'PARTNER'}
    )
    organization = models.CharField(max_length=255, blank=True)
    partnership_level = models.CharField(
        max_length=50, blank=True, help_text='e.g. Gold, Silver, Bronze'
    )

    @property
    def slug_source(self):
        return self.organization or self.user.get_full_name()

    def __str__(self):
        return f"Partner: {self.organization or self.user.get_full_name()}"

