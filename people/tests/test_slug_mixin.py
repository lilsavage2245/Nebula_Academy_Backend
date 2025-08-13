from django.utils.text import slugify
from datetime import datetime
from people.models import Expertise, LecturerProfile, ProgramDirectorProfile, VolunteerProfile, BloggerProfile, PartnerProfile
from core.models import User
import pytest

# Creating test data for User since all Profiles are tied to Users
def create_test_user(email, first_name, last_name, role):
    return User.objects.create_user(
        email=email,
        first_name=first_name,
        last_name=last_name,
        password="testpass123",
        role=role
    )

# Tests for Expertise slug generation
@pytest.mark.django_db
def test_expertise_slug_collision_generates_unique_suffix():
    e1 = Expertise.objects.create(name="Data & AI")
    e2 = Expertise.objects.create(name="Data AI")  # both produce "data-ai" when slugified

    assert e1.slug == "data-ai"
    assert e2.slug.startswith("data-ai-")
    assert e1.slug != e2.slug

# LecturerProfile
@pytest.mark.django_db
def test_lecturer_profile_slug_generation():
    user = create_test_user("lecturer1@example.com", "Ada", "Obi", "LECTURER")
    profile = LecturerProfile.objects.create(user=user)
    assert profile.slug == slugify(user.get_full_name())

# BloggerProfile with pen_name
@pytest.mark.django_db
def test_blogger_profile_with_pen_name_slug():
    user = create_test_user("blogger@example.com", "Sola", "James", "BLOGGER")
    profile = BloggerProfile.objects.create(user=user, pen_name="CodeQueen")
    assert profile.slug == slugify("CodeQueen")

# BloggerProfile fallback to full name
@pytest.mark.django_db
def test_blogger_profile_fallback_slug():
    user = create_test_user("writer@example.com", "Timi", "George", "BLOGGER")
    profile = BloggerProfile.objects.create(user=user)
    assert profile.slug == slugify(user.get_full_name())

# PartnerProfile with organization name
@pytest.mark.django_db
def test_partner_profile_slug_with_org():
    user = create_test_user("partner@example.com", "Ngozi", "Smith", "PARTNER")
    profile = PartnerProfile.objects.create(user=user, organization="Nebula Partners")
    assert profile.slug == slugify("Nebula Partners")

# PartnerProfile fallback to user name
@pytest.mark.django_db
def test_partner_profile_slug_fallback():
    user = create_test_user("partner2@example.com", "Kunle", "Ade", "PARTNER")
    profile = PartnerProfile.objects.create(user=user)
    assert profile.slug == slugify(user.get_full_name())

# VolunteerProfile
@pytest.mark.django_db
def test_volunteer_profile_slug_generation():
    user = create_test_user("volunteer@example.com", "Chika", "Umeh", "VOLUNTEER")
    profile = VolunteerProfile.objects.create(user=user)
    assert profile.slug == slugify(user.get_full_name())

# ProgramDirectorProfile
@pytest.mark.django_db
def test_director_profile_slug_generation():
    user = create_test_user("admin@example.com", "Farida", "Omar", "ADMIN")
    profile = ProgramDirectorProfile.objects.create(user=user)
    assert profile.slug == slugify(user.get_full_name())
