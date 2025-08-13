import pytest
from achievement.models import Badge
from achievement.models import badge_image_upload_path

@pytest.mark.django_db
def test_slug_is_generated_on_creation():
    badge = Badge.objects.create(name="Top Coder")
    assert badge.slug == "top-coder"

@pytest.mark.django_db
def test_slug_collision_creates_unique_slug():
    b1 = Badge.objects.create(name="Top Coder")
    b2 = Badge.objects.create(name="Top Coder")
    assert b1.slug == "top-coder"
    assert b2.slug.startswith("top-coder-")
    assert b1.slug != b2.slug

@pytest.mark.django_db
def test_slug_does_not_change_on_name_update():
    badge = Badge.objects.create(name="Fast Learner")
    original_slug = badge.slug
    badge.name = "Updated Name"
    badge.save()
    assert badge.slug == original_slug  # Slug should remain unchanged

@pytest.mark.django_db
def test_badge_image_upload_path_uses_slug():
    badge = Badge.objects.create(name="Upload Tester")
    filename = "example.png"
    path = badge_image_upload_path(badge, filename)
    assert path == f"achievement/badges/{badge.slug}/{filename}"

from django.utils.text import slugify

@pytest.mark.django_db
def test_slug_truncation_and_suffix_on_collision():
    long_name = "X" * 110
    badge1 = Badge.objects.create(name=long_name)
    badge2 = Badge.objects.create(name=long_name)

    # Slugs should be unique
    assert badge1.slug != badge2.slug

    # Both slugs must be within the max allowed length
    assert len(badge1.slug) <= 100
    assert len(badge2.slug) <= 100

    # Generate the expected base slug manually (this is what your mixin would base its slug on)
    expected_base = slugify(long_name)[:100 - 2]  # 2 chars reserved for "-2" suffix

    # Now check if badge2.slug starts with this base
    assert badge2.slug.startswith(expected_base)
