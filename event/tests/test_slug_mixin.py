# event/tests/test_slug_mixin.py
import pytest
from django.utils import timezone
from event.models import Event, EventCategory

@pytest.mark.django_db
def test_event_slug_is_generated_from_title():
    event1 = Event.objects.create(title="Nebula Tech Week", start_datetime=timezone.now())
    event2 = Event.objects.create(title="Nebula Tech Week", start_datetime=timezone.now())

    assert event1.slug == "nebula-tech-week"
    assert event2.slug.startswith("nebula-tech-week-")
    assert event1.slug != event2.slug

@pytest.mark.django_db
def test_event_slug_is_preserved_on_update():
    event = Event.objects.create(title="AI for Africa", start_datetime=timezone.now())
    original_slug = event.slug

    event.title = "Updated Title"
    event.save()

    assert event.slug == original_slug  # Slug should not change

@pytest.mark.django_db
def test_event_slug_trims_long_titles():
    long_title = "Nebula " + ("Future " * 20) + "Hackathon"
    event = Event.objects.create(title=long_title, start_datetime=timezone.now())

    assert len(event.slug) <= 200
    assert event.slug.startswith("nebula-future")

@pytest.mark.django_db
def test_event_published_on_is_set_when_published():
    event = Event.objects.create(
        title="DevCon",
        start_datetime=timezone.now(),
        is_published=True,
        published_on=None,
    )
    assert event.published_on is not None

# -----------------------
# EventCategory Tests
# -----------------------

@pytest.mark.django_db
def test_event_category_slug_generation():
    cat1 = EventCategory.objects.create(name="Parent Webinars")
    cat2 = EventCategory.objects.create(name="Parent Webinars 2025")

    assert cat1.slug == "parent-webinars"
    assert cat2.slug.startswith("parent-webinars")
    assert cat1.slug != cat2.slug

@pytest.mark.django_db
def test_event_category_slug_preserved_on_update():
    category = EventCategory.objects.create(name="Tech Events")
    original_slug = category.slug

    category.name = "Updated Events"
    category.save()

    assert category.slug == original_slug
