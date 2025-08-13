# program/tests/test_program_slug.py

import pytest
from program.models import Program, ProgramCategory

@pytest.mark.django_db
def test_program_slug_is_generated():
    program = Program.objects.create(
        name="Beginner Track",
        category=ProgramCategory.BEGINNER
    )
    assert program.slug == "beginner-track-beg"

@pytest.mark.django_db
def test_program_slug_uniqueness_with_duplicate_name_and_category():
    program1 = Program.objects.create(name="AI Program", category=ProgramCategory.ADVANCED)
    program2 = Program.objects.create(name="AI Program", category=ProgramCategory.BEGINNER)

    assert program1.slug == "ai-program-adv"
    assert program2.slug == "ai-program-beg"
    assert program1.slug != program2.slug


@pytest.mark.django_db
def test_program_slug_persists_after_update():
    program = Program.objects.create(name="Cybersecurity", category=ProgramCategory.INTER_DIP)
    old_slug = program.slug
    program.name = "Cybersecurity Advanced"
    program.save()
    assert program.slug == old_slug  # Slug shouldn't change on name update

@pytest.mark.django_db
def test_program_slug_max_length_trimmed():
    long_name = "A" * 200  # deliberately long
    program = Program.objects.create(name=long_name, category=ProgramCategory.PRE_ACADEMY)
    assert len(program.slug) <= 100  # respect max_length
