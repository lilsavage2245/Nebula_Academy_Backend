import pytest
import io
from rest_framework.test import APIClient
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from program.models import ProgramLevel, Program
from module.models import Module, LectureMaterial, ModuleLecturer
from module.serializers import (
    ModuleCreateUpdateSerializer,
    ModuleSerializer,
    LectureMaterialSerializer,
    ModuleLecturerSerializer
)
from rest_framework.exceptions import ValidationError

User = get_user_model()

# ---------- Helpers ----------
@pytest.fixture
def lecturer():
    return User.objects.create_user(
        email="lecturer@example.com",
        password="pass1234",
        role="LECTURER",
        first_name="Test",
        last_name="Lecturer"
    )

@pytest.fixture
def student():
    return User.objects.create_user(
        email="student@example.com",
        password="pass1234",
        role="STUDENT",
        first_name="Student",
        last_name="User"
    )

@pytest.fixture
def program():
    return Program.objects.create(
        name="Test Program",
        category="PRE",  # Or whatever is valid in your ProgramCategory
        description="Test description"
    )

@pytest.fixture
def level(program):
    return ProgramLevel.objects.create(
        program=program,
        title="Level 1",
        level_number=1,
        description="Entry level"
    )


@pytest.fixture
def pdf_file():
    return SimpleUploadedFile("lecture.pdf", b"%PDF-1.4 test content", content_type="application/pdf")

# ---------- Tests ----------

@pytest.mark.django_db
def test_module_create_with_nested_levels_and_lecturers(lecturer, level):
    data = {
        "title": "AI & Robotics",
        "description": "Intro course",
        "is_standalone": True,
        "levels": [{"level_id": level.id, "order": 1}],
        "lecturers": [{"lecturer_id": lecturer.id, "role": "Primary"}]
        # Note: no materials here
    }

    serializer = ModuleCreateUpdateSerializer(data=data)
    assert serializer.is_valid(), serializer.errors
    module = serializer.save()

    # ✅ Create LectureMaterial in second step
    from django.core.files.uploadedfile import SimpleUploadedFile
    pdf_file = SimpleUploadedFile("lecture.pdf", b"%PDF-1.4 test content", content_type="application/pdf")

    from module.models import LectureMaterial
    material = LectureMaterial.objects.create(
        module=module,
        title="Week 1",
        audience="FREE",
        slides=pdf_file,
        video_url="https://youtu.be/abc123"
    )

    assert module.title == "AI & Robotics"
    assert module.modulelevellink_set.count() == 1
    assert module.modulelecturer_set.count() == 1
    assert module.materials.count() == 1
    serializer = LectureMaterialSerializer(material)
    assert serializer.data["file_type"] == "pdf"


@pytest.mark.django_db
def test_lecture_material_file_size_and_type(pdf_file):
    module = Module.objects.create(title="Test Module", description="...", is_standalone=True)
    material = LectureMaterial.objects.create(
        module=module,
        title="Slides",
        audience="FREE",
        slides=pdf_file,
        video_url=""
    )
    serializer = LectureMaterialSerializer(instance=material)
    data = serializer.data

    assert data["file_type"] == "pdf"
    assert data["file_size"] > 0

@pytest.mark.django_db
def test_module_serializer_outputs_expected_fields():
    module = Module.objects.create(title="Web Dev", description="HTML/CSS", is_standalone=False)
    serializer = ModuleSerializer(instance=module)
    data = serializer.data

    assert data["slug"] == module.slug
    assert data["title"] == "Web Dev"
    assert isinstance(data["levels"], list)
    assert isinstance(data["materials"], list)
    assert isinstance(data["evaluations"], list)

@pytest.mark.django_db
def test_module_lecturer_serializer_rejects_invalid_role(student):
    data = {
        "lecturer_id": student.id,
        "role": "Primary"
    }
    serializer = ModuleLecturerSerializer(data=data)

    with pytest.raises(ValidationError):
        serializer.is_valid(raise_exception=True)


@pytest.mark.django_db
def test_module_create_with_materials_full_stack(lecturer, level):
    client = APIClient()
    client.force_authenticate(user=lecturer)

    file_data = SimpleUploadedFile("week1.pdf", b"%PDF-1.4 content", content_type="application/pdf")
    payload = {
        "title": "Deep Learning",
        "description": "Advanced AI",
        "is_standalone": True,
        "levels": [{"level_id": level.id, "order": 1}],
        "lecturers": [{"lecturer_id": lecturer.id, "role": "Primary"}],
        "materials": [{
            "title": "Lecture Slides",
            "audience": "FREE",
            "slides": file_data,
            "video_url": "https://youtu.be/abc123"
        }]
    }

    response = client.post("/api/modules/", data=payload, format="multipart")
    assert response.status_code == 201, response.content
    assert response.data["title"] == "Deep Learning"
    assert response.data["materials"][0]["file_type"] == "pdf"

@pytest.mark.django_db
def test_module_update_serializer_changes_title_and_lecturers(lecturer, level):
    module = Module.objects.create(title="Old Title", description="desc", is_standalone=False)
    ModuleLecturer.objects.create(module=module, lecturer=lecturer, role="Primary")

    new_lecturer = User.objects.create_user(email="new@lecturer.com", password="pass", role="LECTURER", first_name="New", last_name="Lecturer")

    data = {
        "title": "New Title",
        "description": "Updated desc",
        "is_standalone": True,
        "lecturers": [{"lecturer_id": new_lecturer.id, "role": "Assistant"}]
    }

    serializer = ModuleCreateUpdateSerializer(instance=module, data=data)
    assert serializer.is_valid(), serializer.errors
    updated = serializer.save()

    assert updated.title == "New Title"
    assert updated.modulelecturer_set.count() == 1
    assert updated.modulelecturer_set.first().lecturer == new_lecturer

@pytest.mark.django_db
def test_module_slug_is_preserved_on_update():
    module = Module.objects.create(title="Original Title", description="Test", is_standalone=True)
    original_slug = module.slug

    module.title = "New Title"
    module.save()

    assert module.slug == original_slug
