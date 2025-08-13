# tests/test_quiz.py
import pytest
from django.contrib.auth import get_user_model
from classes.models import (
    Lesson, LessonQuiz, LessonQuizQuestion,
    LessonQuizResult, LessonQuizAnswer
)
from django.utils.timezone import now

User = get_user_model()

@pytest.mark.django_db
def test_lesson_quiz_submission_flow():
    # Create user and lesson
    user = User.objects.create_user(email="student@example.com", password="pass1234", first_name="Malachi", last_name="Agabus")
    lesson = Lesson.objects.create(title="Sample Lesson", slug="sample-lesson", date=now(), )

    # Create quiz
    quiz = LessonQuiz.objects.create(lesson=lesson, title="Intro Quiz")

    # Add questions
    q1 = LessonQuizQuestion.objects.create(
        quiz=quiz,
        text="What is 2 + 2?",
        choices=["3", "4", "5"],
        correct_answer="4"
    )
    q2 = LessonQuizQuestion.objects.create(
        quiz=quiz,
        text="Which planet is known as the Red Planet?",
        choices=["Earth", "Mars", "Venus"],
        correct_answer="Mars"
    )

    # User takes quiz
    result = LessonQuizResult.objects.create(user=user, quiz=quiz)

    # Answer Q1 correctly, Q2 incorrectly
    LessonQuizAnswer.objects.create(
        result=result, question=q1,
        selected_answer="4", is_correct=True
    )
    LessonQuizAnswer.objects.create(
        result=result, question=q2,
        selected_answer="Venus", is_correct=False
    )

    # Update result
    result.score = LessonQuizAnswer.objects.filter(result=result, is_correct=True).count()
    result.passed = result.score >= 1  # passing threshold = 1
    result.save()

    assert result.score == 1
    assert result.passed is True
    assert result.quiz == quiz
    assert result.user == user

    # Double check answers linkage
    assert result.answers.count() == 2
