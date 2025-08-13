# classes/tests/test_quiz_extended.py
import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from classes.models import LessonQuizResult
from django.utils import timezone

@pytest.mark.django_db
class TestLessonQuizEdgeCases:

    def setup_method(self):
        self.client = APIClient()
        self.user = self._create_user("failtest@example.com")
        self.client.force_authenticate(user=self.user)
        self.lesson = self._create_lesson()
        self.quiz = self._create_quiz(self.lesson)
        self.question1 = self._create_question(self.quiz, "What is 2+2?", ["2", "4", "6"], "4")
        self.question2 = self._create_question(self.quiz, "What is 3+3?", ["3", "5", "6"], "6")
        self.submit_url = reverse('quiz-result-submit', args=[self.quiz.id])

    def _create_user(self, email):
        from django.contrib.auth import get_user_model
        return get_user_model().objects.create_user(email=email, password="pass1234", first_name="Tiwa", last_name="Savage")

    def _create_lesson(self):
        from classes.models import Lesson
        return Lesson.objects.create(
            title="Quiz Lesson", description="", date=timezone.now(), is_published=True
        )

    def _create_quiz(self, lesson):
        from classes.models import LessonQuiz
        return LessonQuiz.objects.create(lesson=lesson, title="Test Quiz", description="")

    def _create_question(self, quiz, text, choices, correct_answer):
        from classes.models import LessonQuizQuestion
        return LessonQuizQuestion.objects.create(quiz=quiz, text=text, choices=choices, correct_answer=correct_answer)

    def test_user_fails_quiz(self):
        data = {
            "answers": [
                {"question_id": self.question1.id, "selected_answer": "2"},  # incorrect
                {"question_id": self.question2.id, "selected_answer": "5"},  # incorrect
            ]
        }
        response = self.client.post(self.submit_url, data, format="json")
        print("Duplicate submission:", response.status_code, response.data)
        assert response.status_code == 201
        result = LessonQuizResult.objects.get(user=self.user, quiz=self.quiz)
        assert result.score == 0
        assert result.passed is False

    def test_partial_answers(self):
        data = {
            "answers": [
                {"question_id": self.question1.id, "selected_answer": "4"},  # correct
            ]
        }
        response = self.client.post(self.submit_url, data, format="json")
        print("Duplicate submission:", response.status_code, response.data)
        assert response.status_code == 201
        result = LessonQuizResult.objects.get(user=self.user, quiz=self.quiz)
        assert result.score == 1
        assert result.passed is False

    def test_inactive_quiz(self):
        self.quiz.is_active = False
        self.quiz.save()
        data = {
            "answers": [
                {"question_id": self.question1.id, "selected_answer": "4"},
                {"question_id": self.question2.id, "selected_answer": "6"},
            ]
        }
        response = self.client.post(self.submit_url, data, format="json")
        print("Duplicate submission:", response.status_code, response.data)
        assert response.status_code == 400
        assert "not currently active" in str(response.data["detail"]).lower()

    def test_duplicate_submission(self):
        # Submit once
        data = {
            "answers": [
                {"question_id": self.question1.id, "selected_answer": "4"},
                {"question_id": self.question2.id, "selected_answer": "6"},
            ]
        }
        self.client.post(self.submit_url, data, format="json")

        # Submit again — should fail due to unique_together constraint
        response = self.client.post(self.submit_url, data, format="json")
        print("Duplicate submission:", response.status_code, response.data)
        assert response.status_code in [400, 409]
        assert (
            "already submitted" in str(response.data).lower()
            or "unique" in str(response.data).lower()
        )
