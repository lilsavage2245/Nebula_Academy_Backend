import pytest
from django.utils import timezone
from worksheet.models import Worksheet
from classes.models import Lesson
from core.models import User  # or wherever your custom User model is

@pytest.mark.django_db
def test_worksheet_slug_is_generated_from_title():
    lesson = Lesson.objects.create(
        title="Intro to Loops",
        description="Lesson desc",
        date=timezone.now()
    )
    user = User.objects.create_user(
        email="lecturer@example.com",
        first_name="Jane",
        last_name="Doe",
        password="test1234",
        role="LECTURER"
    )
    worksheet = Worksheet.objects.create(
        title="While Loops Worksheet",
        class_session=lesson,
        uploaded_by=user
    )
    assert worksheet.slug == "while-loops-worksheet"

@pytest.mark.django_db
def test_slug_uniqueness_is_enforced():
    lesson = Lesson.objects.create(
        title="Conditionals",
        description="Lesson on if-else",
        date=timezone.now()
    )
    user = User.objects.create_user(
        email="teacher@example.com",
        first_name="Tom",
        last_name="Jerry",
        password="pass1234",
        role="LECTURER"
    )
    w1 = Worksheet.objects.create(
        title="Decision Trees",
        class_session=lesson,
        uploaded_by=user
    )
    w2 = Worksheet.objects.create(
        title="Decision Trees",
        class_session=lesson,
        uploaded_by=user
    )
    assert w1.slug == "decision-trees"
    assert w2.slug.startswith("decision-trees-")
    assert w1.slug != w2.slug

@pytest.mark.django_db
def test_slug_is_not_changed_on_title_update():
    lesson = Lesson.objects.create(
        title="Data Types",
        description="Lesson desc",
        date=timezone.now()
    )
    user = User.objects.create_user(
        email="update@example.com",
        first_name="Ada",
        last_name="Lovelace",
        password="pass456",
        role="LECTURER"
    )
    worksheet = Worksheet.objects.create(
        title="Variables",
        class_session=lesson,
        uploaded_by=user
    )
    original_slug = worksheet.slug
    worksheet.title = "Updated Title"
    worksheet.save()

    assert worksheet.slug == original_slug  # Confirm slug remains unchanged after update

@pytest.mark.django_db
def test_slug_respects_max_length():
    lesson = Lesson.objects.create(
        title="Title Cap Test",
        description="Lesson desc",
        date=timezone.now()
    )
    user = User.objects.create_user(
        email="longslug@example.com",
        first_name="Max",
        last_name="Length",
        password="pass789",
        role="LECTURER"
    )
    long_title = "This is a very long worksheet title that should be truncated properly to meet the slug field length limit"
    worksheet = Worksheet.objects.create(
        title=long_title,
        class_session=lesson,
        uploaded_by=user
    )

    assert len(worksheet.slug) <= Worksheet._meta.get_field("slug").max_length
