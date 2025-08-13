import pytest
from support.models import SupportCategory, SupportTopic

@pytest.mark.django_db
def test_support_category_slug_generation():
    c1 = SupportCategory.objects.create(name="Technical Support")
    c2 = SupportCategory.objects.create(name="Technical Support Copy")

    assert c1.slug == "technical-support"
    assert c2.slug.startswith("technical-support-copy")
    assert c1.slug != c2.slug

@pytest.mark.django_db
def test_support_topic_slug_generation():
    category = SupportCategory.objects.create(name="Login Help")
    t1 = SupportTopic.objects.create(title="Can't reset my password", category=category)
    t2 = SupportTopic.objects.create(title="Can't reset my password", category=category)

    assert t1.slug == "cant-reset-my-password"
    assert t2.slug.startswith("cant-reset-my-password-")
    assert t1.slug != t2.slug

