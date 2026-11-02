from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from unused_scripts.image_task_assignment import TaskAssigner
from apps.project_management.models.plan_members import PlanMember

from apps.project_management.models.image_plan import ImagePlan


class AssignTasksAPIView(APIView):
    """
    Manages the assignment of Workers to Tasks.
    Creates 'ImageAnnotationTask' records.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, batch_id, *args, **kwargs):
        try:
            batch = ImagePlan.objects.get(id=batch_id)
        except ImagePlan.DoesNotExist:
            return Response({"detail": "Batch not found."}, status=404)

        if batch.created_by != request.user.id:
            return Response({"detail": "Permission denied."}, status=403)

        # The Assigner now works on the Batch level
        assigner = TaskAssigner(batch)

        # This function should:
        # 1. Find all ImageBatchTasks in the batch
        # 2. Find all BatchMembers (Annotators)
        # 3. Create ImageAnnotationTask links between them
        assigned_count = assigner.assign_all_pending()

        return Response({
            "message": "Tasks assigned successfully.",
            "new_assignments": assigned_count
        })


class ManualReassignTasksAPIView(APIView):
    """
    Manually force an assignment for a specific annotator.
    Useful if a worker requests 'More Work'.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, batch_id, annotator_id, *args, **kwargs):
        try:
            batch = ImagePlan.objects.get(id=batch_id)
        except ImagePlan.DoesNotExist:
            return Response({"error": "Batch not found."}, status=404)

        # Find the specific worker
        annotator = PlanMember.objects.filter(
            profile=annotator_id,
            batch=batch,
            role="ANNOTATOR",  # Ensure this matches your Choices
        ).first()

        if not annotator:
            return Response({"error": "Annotator not found in this batch."}, status=404)

        assigner = TaskAssigner(batch)

        # Helper to assign X new tasks to this specific user
        # Creates ImageAnnotationTask entries
        assigned_tasks = assigner.assign_next_tasks_to_worker(annotator, count=10)

        return Response(
            {
                "message": f"Assigned {len(assigned_tasks)} new tasks to {annotator}.",
                "assigned_ids": [t.id for t in assigned_tasks]
            }
        )