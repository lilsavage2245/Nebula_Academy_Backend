# dashboard/views/free

from urllib import request
import urllib.parse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils.timezone import now
from collections import defaultdict
from datetime import timedelta
from django.shortcuts import get_object_or_404
from engagement.models import EngagementPing

from dashboard.serializers.free import FreeDashboardOverviewSerializer
from dashboard.models import FreeStudentDashboard, DashboardSetting
from django.db import models
from django.db.models import Sum
from classes.models import LessonAttendance, Lesson
from achievement.models import AwardedBadge
from worksheet.models import WorksheetSubmission
#from news.models import DashboardArticle  # for weekly tasks (e.g., write article)
from dashboard.utils.active_time import get_weekly_learning_minutes
from dashboard.serializers.free import LessonDetailInModuleSerializer
from module.models import Module

# tasks
from badgetasks.services.evaluator import evaluate_weekly_tasks_for_user
from badgetasks.models import WeeklyTaskAssignment

def _get_profile_picture_url(user):
    if getattr(user, "profile_picture", None):
        try:
            return user.profile_picture.url
        except ValueError:
            pass  # in case the file field is empty/invalid
    # fallback: UI Avatars with initials
    name = user.get_full_name() or user.first_name or "User"
    encoded_name = urllib.parse.quote_plus(name)
    return f"https://ui-avatars.com/api/?name={encoded_name}&background=random&color=fff"


def _weekly_minutes_last_7_days(user):
    """Return dict of Mon..Sun -> total 'active minutes' = pings + lesson minutes."""
    start = (now() - timedelta(days=6)).date()

    # 1) Ping minutes (each unique user+minute = 1 minute)
    ping_rows = (
        EngagementPing.objects
        .filter(user=user, minute__date__gte=start)
        .values_list("minute", flat=True)
    )
    ping_daily = {"Mon":0,"Tue":0,"Wed":0,"Thu":0,"Fri":0,"Sat":0,"Sun":0}
    for m in ping_rows:
        ping_daily[m.strftime("%a")] += 1

    # 2) Lesson minutes
    lesson_rows = (
        LessonAttendance.objects
        .filter(user=user, timestamp__date__gte=start)
        .values("timestamp", "duration")
    )
    lesson_daily = {"Mon":0,"Tue":0,"Wed":0,"Thu":0,"Fri":0,"Sat":0,"Sun":0}
    for r in lesson_rows:
        lesson_daily[r["timestamp"].strftime("%a")] += r["duration"] or 0

    # 3) Sum
    weekly = {}
    for k in ping_daily.keys():
        weekly[k] = ping_daily[k] + lesson_daily[k]
    return weekly


def _map_status(status_str):
    """Map model status (PENDING/IN_PROGRESS/COMPLETED) -> frontend-friendly."""
    s = (status_str or "").upper()
    if s == "COMPLETED":
        return "completed"
    if s == "IN_PROGRESS":
        return "in_progress"
    return "pending"

class FreeDashboardOverviewAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        # Safe fallbacks if objects aren’t created yet
        dashboard, _ = FreeStudentDashboard.objects.get_or_create(
            user=user,
            defaults={
                "program_level": "BEGINNER",
                "age": 0,
                "personalised_class_filter": "ALL",
                "theme_preference": "LIGHT",
            },
        )
        settings, _ = DashboardSetting.objects.get_or_create(
            user=user,
            defaults={"theme": "LIGHT", "content_filter": "ALL", "show_survey_popup": True},
        )

        # Lessons Completed
        completed_lessons = (
            LessonAttendance.objects
            .filter(user=user, attended=True)
            .values_list("lesson_id", flat=True)
            .distinct()
            .count()
        )

        # Modules In Progress
        modules_in_progress = (
            LessonAttendance.objects
            .filter(user=user, attended=True, lesson__module__isnull=False)
            .values("lesson__module_id")
            .distinct()
            .count()
        )

        # Total Learning Time
        total_minutes = (
            LessonAttendance.objects
            .filter(user=user)
            .aggregate(total=Sum("duration"))
            .get("total") or 0
        )
        total_learning_time = f"{total_minutes // 60}h {total_minutes % 60}m"

        # Weekly activity (last 7 days)
        weekly_activity = _weekly_minutes_last_7_days(user)

        # Badges
        badges = AwardedBadge.objects.filter(user=user).select_related("badge")
        badges_earned = [{"title": b.badge.title, "icon": b.badge.icon or "🏅"} for b in badges]

        # If you want TIME_SPENT to include EngagementPing minutes, set flag True:
        evaluate_weekly_tasks_for_user(request.user, include_active_minutes_in_time_spent=False)
        task_qs = WeeklyTaskAssignment.objects.filter(user=user).select_related("task")
        weekly_tasks = [
            {
                "title": ta.task.title,
                "type": ta.task.task_type,
                "required_hours": ta.task.required_hours,
                "status": _map_status(ta.status),
                "progress": ta.progress or {},
            }
            for ta in task_qs
        ]

        # Construct response
        data = {
            "first_name": user.first_name,
            "email": user.email,
            "profile_picture": _get_profile_picture_url(user),
            "location": getattr(user, "location", None),
            "joined_date": user.date_joined.date(),
            "program_level": dashboard.program_level,
            "completed_lessons": completed_lessons,
            "modules_in_progress": modules_in_progress,
            "total_learning_time": total_learning_time,
            "weekly_activity": weekly_activity,
            "badges_earned": badges_earned,
            "weekly_tasks": weekly_tasks,
            "theme_preference": settings.theme,
            "content_filter": settings.content_filter,
        }

        serializer = FreeDashboardOverviewSerializer(data)
        return Response(serializer.data)


class FreeLessonStatsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        dashboard = user.dashboard  # FreeStudentDashboard via OneToOne

        program_level = dashboard.program_level
        now_time = now()

        # Filter eligible lessons for this user
        base_lessons_qs = Lesson.objects.filter(
            audience__in=["FREE", "BOTH"],
            program_level=program_level
        )

        upcoming_lessons = base_lessons_qs.filter(delivery_date__gt=now_time).count()
        past_lessons_qs = base_lessons_qs.filter(delivery_date__lte=now_time)

        # Attendance check
        attended_ids = set(
            LessonAttendance.objects.filter(
                user=user, attended=True
            ).values_list("lesson_id", flat=True)
        )

        attended_count = past_lessons_qs.filter(id__in=attended_ids).count()
        unattended_count = past_lessons_qs.exclude(id__in=attended_ids).count()

        return Response({
            "upcoming_lessons": upcoming_lessons,
            "past_lessons": past_lessons_qs.count(),
            "attended_lessons": attended_count,
            "unattended_past_lessons": unattended_count
        })

class FreeModulesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        dashboard = user.dashboard  # FreeStudentDashboard

        # Step 1: Get all lessons this user has attended
        attended_lesson_ids = (
            LessonAttendance.objects
            .filter(user=user, attended=True)
            .values_list('lesson_id', flat=True)
        )

        if not attended_lesson_ids:
            return Response([])

        # Step 2: Get attended lessons that are marked FREE/BOTH and match user's level
        lessons = (
            Lesson.objects
            .filter(
                id__in=attended_lesson_ids,
                audience__in=["FREE", "BOTH"],
                program_level=dashboard.program_level
            )
            .select_related('module')
            .order_by('-date')
        )

        # Step 3: Group by module
        modules_map = {}
        for lesson in lessons:
            module = lesson.module
            if not module:
                continue
            if module.id not in modules_map:
                modules_map[module.id] = {
                    "module_id": module.id,
                    "title": module.title,
                    "slug": module.slug,
                    "lessons": []
                }

            # Get attendance object to fetch `timestamp` (i.e., when user viewed)
            attendance = LessonAttendance.objects.filter(user=user, lesson=lesson).first()
            modules_map[module.id]["lessons"].append({
                "lesson_id": lesson.id,
                "title": lesson.title,
                "viewed_at": attendance.timestamp if attendance else None
            })

        return Response(list(modules_map.values()))    

class ModuleLessonsDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, slug):
        user = request.user
        dashboard = user.dashboard

        module = get_object_or_404(Module, slug=slug)

        # Get all attended lesson IDs
        attended_ids = (
            LessonAttendance.objects
            .filter(user=user, attended=True)
            .values_list("lesson_id", flat=True)
        )

        lessons = (
            Lesson.objects
            .filter(
                id__in=attended_ids,
                module=module,
                audience__in=["FREE", "BOTH"],
                program_level=dashboard.program_level
            )
            .select_related('module')
            .order_by('-date')
        )

        # Map results
        results = []
        for lesson in lessons:
            attendance = LessonAttendance.objects.filter(user=user, lesson=lesson).first()
            results.append({
                "lesson_id": lesson.id,
                "title": lesson.title,
                "date": lesson.date,
                "delivery": lesson.delivery,
                "delivery_display": lesson.get_delivery_display(),
                "viewed_at": attendance.timestamp if attendance else None,
                "video_embed_url": lesson.video_embed_url,
                "worksheet_link": lesson.worksheet_link,
                "has_comment_access": lesson.allow_comments,
                "has_rating_access": lesson.allow_ratings,
            })

        return Response(LessonDetailInModuleSerializer(results, many=True).data)