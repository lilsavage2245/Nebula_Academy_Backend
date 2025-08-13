from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from badgetasks.models import WeeklyTaskAssignment
from badgetasks.serializers.task import WeeklyTaskAssignmentSerializer
from badgetasks.services.evaluator import evaluate_weekly_tasks_for_user


class WeeklyTaskListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # Always update task status before showing
        evaluate_weekly_tasks_for_user(user)

        tasks = WeeklyTaskAssignment.objects.filter(user=user).select_related('task')
        serializer = WeeklyTaskAssignmentSerializer(tasks, many=True)
        return Response(serializer.data)
