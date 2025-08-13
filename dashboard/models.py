# dashboard/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone


class BaseDashboard(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class FreeStudentDashboard(BaseDashboard):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='free_dashboard'
    )
    program_level = models.CharField(
        max_length=50,
        choices=[
            ('PRE_ACADEMY', 'Pre-Academy'),
            ('BEGINNER', 'Beginner'),
            ('INTERMEDIATE', 'Intermediate'),
            ('ADVANCED', 'Advanced'),
        ]
    )
    age = models.PositiveIntegerField()
    personalised_class_filter = models.CharField(
        max_length=20,
        choices=[
            ('ALL', 'All Classes'),
            ('NEBULA_ONLY', 'Only Nebula Lecturers'),
            ('GUEST_ONLY', 'Only Guest Facilitators')
        ],
        default='ALL'
    )
    theme_preference = models.CharField(
        max_length=20,
        choices=[('LIGHT', 'Light'), ('DARK', 'Dark')],
        default='LIGHT'
    )

    def __str__(self):
        return f"Free Student Dashboard for {self.user.email}"


class BloggerDashboard(BaseDashboard):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='blogger_dashboard'
    )
    home_address = models.CharField(max_length=255, blank=True)
    show_drafts_first = models.BooleanField(default=True)

    def __str__(self):
        return f"Blogger Dashboard for {self.user.email}"


class DashboardArticle(models.Model):
    DRAFT = 'DRAFT'
    PUBLISHED = 'PUBLISHED'
    STATUS_CHOICES = [
        (DRAFT, 'Draft'),
        (PUBLISHED, 'Published'),
    ]
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='dashboard_articles'
    )
    title = models.CharField(max_length=255)
    content = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.status})"


class ArticleApprovalQueue(models.Model):
    article = models.OneToOneField(
        DashboardArticle,
        on_delete=models.CASCADE,
        related_name='approval_queue'
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='approved_articles'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Approval for: {self.article.title}"


class DashboardSetting(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='dashboard_setting'
    )
    theme = models.CharField(
        max_length=20,
        choices=[('LIGHT', 'Light'), ('DARK', 'Dark')],
        default='LIGHT'
    )
    content_filter = models.CharField(
        max_length=20,
        choices=[
            ('NEBULA_ONLY', 'Only Nebula Lecturers'),
            ('GUEST_ONLY', 'Only Guest Lecturers'),
            ('ALL', 'All Lecturers')
        ],
        default='ALL',
        help_text="Choose content sources to display in dashboard feed"
    )
    show_survey_popup = models.BooleanField(default=True)

    def __str__(self):
        return f"Settings for {self.user.email}"


class DashboardNotification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='dashboard_notifications'
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} to {self.user.email}"
