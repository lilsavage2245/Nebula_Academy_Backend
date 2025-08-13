# dashboard/utils/active_tim
from collections import defaultdict
from django.utils.timezone import now, timedelta
from classes.models import LessonAttendance

def get_weekly_learning_minutes(user):
    today = now().date()
    start_date = today - timedelta(days=6)

    attendance_qs = LessonAttendance.objects.filter(
        user=user,
        timestamp__date__gte=start_date
    ).values('timestamp', 'duration')

    # Prepare empty structure for days
    weekly_minutes = {
        "Mon": 0,
        "Tue": 0,
        "Wed": 0,
        "Thu": 0,
        "Fri": 0,
        "Sat": 0,
        "Sun": 0
    }

    for record in attendance_qs:
        day_label = record['timestamp'].strftime('%a')  # Mon, Tue, etc.
        weekly_minutes[day_label] += record['duration'] or 0

    return weekly_minutes
