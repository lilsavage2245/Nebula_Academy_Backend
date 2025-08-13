# classes/models/quiz.py

from django.db import models
from django.conf import settings
from classes.models.lesson import Lesson


class LessonQuiz(models.Model):
    """
    A quiz attached to a specific lesson.
    """
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='quizzes')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='quizzes_created')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('lesson', 'title')

    def __str__(self):
        return f"{self.title} ({self.lesson.title})"


class LessonQuizQuestion(models.Model):
    """
    A single question with multiple choices.
    """
    quiz = models.ForeignKey(LessonQuiz, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    choices = models.JSONField(help_text='List of options, e.g., ["A", "B", "C", "D"]')
    correct_answer = models.CharField(max_length=255)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"Q: {self.text}"


class LessonQuizResult(models.Model):
    """
    A user's quiz submission attempt.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='lesson_quiz_results')
    quiz = models.ForeignKey(LessonQuiz, on_delete=models.CASCADE, related_name='results')
    score = models.PositiveIntegerField(default=0)
    passed = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-submitted_at']
        unique_together = ('user', 'quiz')  # Optional: limit to one attempt

    def __str__(self):
        return f"{self.user.email} - {self.quiz.title} - {'Passed' if self.passed else 'Failed'}"


class LessonQuizAnswer(models.Model):
    """
    Stores a user's individual answers per question.
    """
    result = models.ForeignKey(LessonQuizResult, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(LessonQuizQuestion, on_delete=models.CASCADE)
    selected_answer = models.CharField(max_length=255)

    is_correct = models.BooleanField(default=False)

    class Meta:
        unique_together = ('result', 'question')

    def __str__(self):
        return f"{self.result.user.email} - {self.question.text[:40]}... - {self.selected_answer}"
