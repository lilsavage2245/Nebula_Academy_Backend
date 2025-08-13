# evaluations/models.py
from django.db import models
from django.conf import settings
from module.models import Module

class EvaluationType(models.TextChoices):
    QUIZ = 'QUIZ', 'Quiz'
    EXAM = 'EXAM', 'Exam'
    PROJECT = 'PROJECT', 'Project'


class Evaluation(models.Model):
    """
    Represents an evaluation task (quiz, exam, or project) for a module.
    """
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='evaluations')
    type = models.CharField(max_length=10, choices=EvaluationType.choices)
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    criteria = models.JSONField(default=dict, help_text="Pass/Grading rules (JSON)")
    weight = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)
    submission_deadline = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['module', 'type']

    def __str__(self):
        return f"{self.module.title} — {self.get_type_display()}: {self.title}"


class EvaluationSubmission(models.Model):
    """
    Stores a student's submission to a given evaluation.
    """
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='evaluation_submissions'
    )
    evaluation = models.ForeignKey(Evaluation, on_delete=models.CASCADE, related_name='submissions')
    submitted_on = models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to='evaluations/submissions/', blank=True, null=True)
    text_response = models.TextField(blank=True)
    notes_to_reviewer = models.TextField(blank=True)

    class Meta:
        unique_together = ('student', 'evaluation')
        ordering = ['-submitted_on']

    def __str__(self):
        return f"{self.student.email} → {self.evaluation.title}"


class EvaluationGrade(models.Model):
    """
    Represents grading and feedback from a staff member.
    """
    submission = models.OneToOneField(EvaluationSubmission, on_delete=models.CASCADE, related_name='grade')
    graded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='graded_evaluations'
    )
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    feedback = models.TextField(blank=True)
    graded_on = models.DateTimeField(auto_now_add=True)
    passed = models.BooleanField(default=False)

    def __str__(self):
        return f"Grade for {self.submission.student.email} on {self.submission.evaluation.title}"
