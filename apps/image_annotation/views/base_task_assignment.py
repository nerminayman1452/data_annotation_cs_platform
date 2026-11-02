from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from unused_scripts.image_task_assignment import TaskAssigner
from apps.project_management.models.plan_members import PlanMember



class BaseAssignTasksAPIView(APIView):
    permission_classes = [IsAuthenticated]

    plan_model = None
    task_type = None

    def post(self, request, plan_id, *args, **kwargs):
        plan = self.plan_model.objects.get(id=plan_id)

        assigner = TaskAssigner(plan, self.task_type)
        assigner.assign_initial_tasks()

        return Response({"message": "Tasks assigned successfully."})


class BaseManualReassignTasksAPIView(APIView):
    permission_classes = [IsAuthenticated]

    plan_model = None
    task_type = None

    def post(self, request, plan_id, annotator_id, *args, **kwargs):
        plan = self.plan_model.objects.get(id=plan_id)

        annotator = PlanMember.objects.filter(
            profile=annotator_id,
            batch=plan.plan,
            user_role="Annotator",
        ).first()

        if not annotator:
            return Response({"error": "Annotator not found."}, status=404)

        assigner = TaskAssigner(plan, self.task_type)
        assigned = assigner.manual_assign_next_tasks(annotator)

        return Response(
            {
                "message": "Manual assignment executed.",
                "assigned_count": len(assigned) if assigned else 0,
            }
        )
