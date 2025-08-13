# certificate/tests/test_slug_mixin.py

import pytest
from certificate.models import CertificateTemplate

pytestmark = pytest.mark.django_db

def test_slug_created_from_title():
    cert = CertificateTemplate.objects.create(title="Nebula Certificate")
    assert cert.slug == "nebula-certificate"

def test_duplicate_slugs_get_incremented():
    c1 = CertificateTemplate.objects.create(title="Nebula Certificate")
    c2 = CertificateTemplate.objects.create(title="Nebula Certificate")
    assert c2.slug.startswith("nebula-certificate-")
    assert c1.slug != c2.slug

def test_slug_does_not_change_on_update():
    cert = CertificateTemplate.objects.create(title="Completion Cert")
    old_slug = cert.slug
    cert.title = "Updated Title"
    cert.save()
    cert.refresh_from_db()
    assert cert.slug == old_slug  # Slug remains unchanged

def test_slug_truncates_to_max_length():
    long_title = "A" * 150  # longer than slug_max_length = 100
    cert = CertificateTemplate.objects.create(title=long_title)
    assert len(cert.slug) <= 100
    assert cert.slug.startswith("a" * 10)  # It’s slugified to lowercase

def test_manual_slug_is_preserved():
    cert = CertificateTemplate.objects.create(title="Some Title", slug="custom-slug")
    assert cert.slug == "custom-slug"
