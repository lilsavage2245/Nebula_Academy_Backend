# core/tests/test_user_slug.py
import pytest
from core.models import User


@pytest.mark.django_db
def test_user_slug_generated_from_email_prefix():
    user = User.objects.create_user(
        email="alice@example.com",
        first_name="Alice",
        last_name="Wonderland",
        password="test123",
        role=User.Roles.FREE
    )
    assert user.slug == "alice"


@pytest.mark.django_db
def test_user_slug_unique_on_collision():
    user1 = User.objects.create_user(
        email="bob@example.com",
        first_name="Bob",
        last_name="Builder",
        password="pass1",
        role=User.Roles.FREE
    )
    user2 = User.objects.create_user(
        email="bob@another.com",
        first_name="Bobby",
        last_name="Builder",
        password="pass2",
        role=User.Roles.FREE
    )
    assert user1.slug == "bob"
    assert user2.slug.startswith("bob-")
    assert user1.slug != user2.slug


@pytest.mark.django_db
def test_user_slug_remains_unchanged_on_update():
    user = User.objects.create_user(
        email="charlie@example.com",
        first_name="Charlie",
        last_name="Chocolate",
        password="candy",
        role=User.Roles.FREE
    )
    original_slug = user.slug
    user.first_name = "Charles"
    user.save()
    assert user.slug == original_slug  # Slug should not regenerate on update


@pytest.mark.django_db
def test_user_slug_source_fallback_when_email_missing():
    user = User.objects.create(
        first_name="No",
        last_name="Email",
        role=User.Roles.FREE,
        is_active=True
    )
    assert user.slug.startswith("no-email")


@pytest.mark.django_db
def test_create_user_raises_if_email_missing():
    with pytest.raises(ValueError):
        User.objects.create_user(
            email=None,
            first_name="No",
            last_name="Email",
            password="test123",
            role=User.Roles.FREE
        )

