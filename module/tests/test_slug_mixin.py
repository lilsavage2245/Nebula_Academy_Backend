# module/tests/test_slug_mixin.py

import pytest
from module.models import Module

@pytest.mark.django_db
def test_slug_mixin_generates_unique_slug():
    module1 = Module.objects.create(title="Python Basics")
    module2 = Module.objects.create(title="Python Basics")

    assert module1.slug == "python-basics"
    assert module2.slug.startswith("python-basics-")
    assert module1.slug != module2.slug

@pytest.mark.django_db
def test_slug_is_preserved_on_title_update():
    module = Module.objects.create(title="Python Basics")
    original_slug = module.slug

    module.title = "Advanced Python"
    module.save()

    assert module.slug == original_slug  # slug stays 

@pytest.mark.django_db
def test_slugify_special_characters():
    module1 = Module.objects.create(title="C++ Basics")
    module2 = Module.objects.create(title="Data & AI")
    module3 = Module.objects.create(title="Learn Python!!")

    assert module1.slug == "c-basics"
    assert module2.slug == "data-ai"
    assert module3.slug == "learn-python"

@pytest.mark.django_db
def test_slug_max_length_enforced():
    long_title = "a" * 200  # 200 chars, but slug_max_length is 150
    module1 = Module.objects.create(title=long_title)
    module2 = Module.objects.create(title=long_title)

    assert len(module1.slug) <= 150
    assert len(module2.slug) <= 150
    assert module1.slug != module2.slug
