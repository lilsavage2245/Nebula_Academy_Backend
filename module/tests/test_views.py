# module/tests/test_views.py
from rest_framework.test import APIClient
from django.urls import reverse
from django.contrib.auth import get_user_model
import pytest
from module.models import Module
from program.models import Program, ProgramLevel

User = get_user_model()

# ---- Fixtures ----
@pytest.fixture
def admin_user():
    return User.objects.create_user(
        email="admin@example.com", password="adminpass", is_staff=True, role="LECTURER", first_name="Admin", last_name="User"
    )

@pytest.fixture
def lecturer_user():
    return User.objects.create_user(
        email="lecturer@example.com", password="pass1234", role="LECTURER", first_name="Test", last_name="Lecturer"
    )

@pytest.fixture
def student_user():
    return User.objects.create_user(
        email="student@example.com", password="pass1234", role="STUDENT", first_name="Student", last_name="User"
    )

@pytest.fixture
def program():
    return Program.objects.create(
        name="Test Program",
        category="PRE",
        description="Testing program"
    )

@pytest.fixture
def level(program):
    return ProgramLevel.objects.create(
        program=program,
        title="Level 1",
        level_number=1,
        description="Test level"
    )

# ---- Tests ----

@pytest.mark.django_db
def test_admin_can_create_module(admin_user):
    client = APIClient()
    client.force_authenticate(user=admin_user)

    data = {
        "title": "Admin Created Module",
        "description": "Test module",
        "is_standalone": True
    }

    response = client.post("/api/modules/", data)
    assert response.status_code == 201
    assert response.data["title"] == "Admin Created Module"

@pytest.mark.django_db
def test_lecturer_cannot_create_module(lecturer_user):
    client = APIClient()
    client.force_authenticate(user=lecturer_user)

    data = {
        "title": "Lecturer Attempt Module",
        "description": "Should fail",
        "is_standalone": False
    }

    response = client.post("/api/modules/", data)
    assert response.status_code == 403

@pytest.mark.django_db
def test_student_cannot_create_module(student_user):
    client = APIClient()
    client.force_authenticate(user=student_user)

    data = {
        "title": "Student Attempt",
        "description": "Should be denied",
        "is_standalone": False
    }

    response = client.post("/api/modules/", data)
    assert response.status_code == 403

@pytest.mark.django_db
def test_everyone_can_view_module(admin_user):
    module = Module.objects.create(title="Visible Module", description="test", is_standalone=True)
    client = APIClient()
    # unauthenticated
    response = client.get(f"/api/modules/{module.slug}/")
    assert response.status_code == 200

    # student
    student = User.objects.create_user(email="s@a.com", password="pass", role="STUDENT", first_name="Student", last_name="User")
    client.force_authenticate(user=student)
    response = client.get(f"/api/modules/{module.slug}/")
    assert response.status_code == 200

"Module view tests ready."
