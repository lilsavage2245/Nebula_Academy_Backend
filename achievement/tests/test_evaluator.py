# achievement/tests/test_evaluator.py

import pytest
from django.contrib.auth import get_user_model
from achievement.models import Badge, AwardedBadge
from achievement.services.evaluator import evaluate_badges_for_user, meets_criteria
from classes.models import LessonAttendance
from worksheet.models import WorksheetSubmission

User = get_user_model()


@pytest.mark.django_db
def test_meets_criteria_worksheets_submitted(academy_universe, test_user):
    worksheet = academy_universe["worksheets"][0]
    badge = Badge.objects.create(
        name='Worksheet Hero', slug='worksheet-hero', is_active=True,
        criteria={'worksheets_submitted': 2}
    )

    WorksheetSubmission.objects.create(user=test_user, worksheet=worksheet)
    WorksheetSubmission.objects.create(user=test_user, worksheet=worksheet)

    assert meets_criteria(test_user, badge.criteria) is True


@pytest.mark.django_db
def test_meets_criteria_lessons_attended(academy_universe, test_user):
    lesson = academy_universe["lessons"][0]
    badge = Badge.objects.create(
        name='Lesson Attender', slug='lesson-attender', is_active=True,
        criteria={'lessons_attended': 1}
    )

    LessonAttendance.objects.create(user=test_user, lesson=lesson, attended=True)

    assert meets_criteria(test_user, badge.criteria) is True


@pytest.mark.django_db
def test_badge_awarded_when_criteria_met(academy_universe, test_user):
    worksheet = academy_universe["worksheets"][0]
    lesson = academy_universe["lessons"][0]

    badge = Badge.objects.create(
        name='Multi Star', slug='multi-star', is_active=True,
        criteria={'lessons_attended': 1, 'worksheets_submitted': 1}, xp_reward=50
    )

    LessonAttendance.objects.create(user=test_user, lesson=lesson, attended=True)
    WorksheetSubmission.objects.create(user=test_user, worksheet=worksheet)

    evaluate_badges_for_user(test_user)

    assert AwardedBadge.objects.filter(user=test_user, badge=badge).exists()
    profile = test_user.profile_achievement
    assert profile.total_xp >= 50


@pytest.mark.django_db
def test_no_duplicate_badge_award(academy_universe, test_user):
    lesson = academy_universe["lessons"][0]
    badge = Badge.objects.create(
        name='Repeat Guard', slug='repeat-guard', is_active=True,
        criteria={'lessons_attended': 1}, xp_reward=10
    )

    LessonAttendance.objects.create(user=test_user, lesson=lesson, attended=True)

    evaluate_badges_for_user(test_user)
    evaluate_badges_for_user(test_user)
    evaluate_badges_for_user(test_user)

    count = AwardedBadge.objects.filter(user=test_user, badge=badge).count()
    assert count == 1
