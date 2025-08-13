# achievement/tests/factories.py

import factory
from django.contrib.auth import get_user_model
from achievement.models import Badge

User = get_user_model()

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
    email = factory.Sequence(lambda n: f"user{n}@test.com")
    password = factory.PostGenerationMethodCall("set_password", "pass1234")

class BadgeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Badge
    name = "Lesson Champ"
    slug = "lesson-champ"
    criteria = {"lessons_attended": 1}
    is_active = True
