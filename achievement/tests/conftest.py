# achievement/tests/conftest.py 

import pytest
from django.contrib.auth import get_user_model
from program.models import Program, ProgramLevel
from module.models import Module, ModuleLevelLink
from classes.models import Lesson
from worksheet.models import Worksheet
from datetime import datetime, timedelta

User = get_user_model()

@pytest.fixture
def academy_universe(db):
    lecturer = User.objects.create_user(
        email="lecturer@example.com",
        password="testpass",
        first_name="Lecturer",
        last_name="One",
        role="LECTURER"
    )

    program = Program.objects.create(
        name="Beginner Program",
        category="BEGINNER",
        description="Basics for all",
        #created_by=lecturer,
        #certificate_title="Beginner Certificate"
    )

    level = ProgramLevel.objects.create(
        program=program,
        level_number=1,
        title="Level 1",
        description="Getting started"
    )

    module = Module.objects.create(
        title="Python Basics",
        description="Learn variables and loops"
    )

    ModuleLevelLink.objects.create(module=module, level=level, order=1)

    # Add 2 Lessons to the Module
    lesson1 = Lesson.objects.create(
        title="Variables 101",
        program_level=level,
        created_by=lecturer,
        delivery="VIDEO",
        audience="FREE",
        session_id="L1"
    )
    lesson2 = Lesson.objects.create(
        title="Loops 101",
        program_level=level,
        created_by=lecturer,
        delivery="VIDEO",
        audience="FREE",
        session_id="L2"
    )

    worksheet1 = Worksheet.objects.create(
        title="Worksheet A",
        description="Test logic",
        lesson=lesson1,
        uploaded_by=lecturer,
        audience="FREE",
        format="FILE"
    )

    worksheet2 = Worksheet.objects.create(
        title="Worksheet B",
        lesson=lesson2,
        uploaded_by=lecturer,
        audience="FREE",
        format="TEXT"
    )

    return {
        "lecturer": lecturer,
        "program": program,
        "level": level,
        "lessons": [lesson1, lesson2],
        "worksheets": [worksheet1, worksheet2]
    }
