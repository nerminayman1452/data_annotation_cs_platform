from apps.image_annotation.models.plan_task import ImagePlanTask
from rest_framework.generics import ListCreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from unused_scripts.image_task_generator import ImageAnnotationTaskGenerator
from apps.image_annotation.serializers.batch_task import ImageBatchTaskSerializer
from apps.project_management.models.image_plan import ImagePlan


class ImageBatchTasksAPIView(ListCreateAPIView):
    """
    Manages the lifecycle of 'Master Items' (BatchTasks).
    GET: List all items in a batch (and their current status).
    POST: Generate items from Raw Data.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ImageBatchTaskSerializer

    def has_access(self, user, batch):
        # Ensure only the batch owner can generate/view administrative tasks
        return batch.created_by == int(user.id)

    # ---------- POST: Generate Batch Tasks from Raw Data ---------- #
    def post(self, request, *args, **kwargs):
        """
        Triggers the conversion of Raw Data (e.g., CSV/Folder) into Database Tasks.
        """
        batch_id = request.data.get("batch")

        if not batch_id:
            return Response({"detail": "batch is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            batch = ImagePlan.objects.get(id=batch_id)
        except ImagePlan.DoesNotExist:
            return Response({"detail": "Batch not found."}, status=status.HTTP_404_NOT_FOUND)

        if not self.has_access(request.user, batch):
            return Response(
                {"detail": "You do not have permission to generate tasks for this batch."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Initialize the Generator (Refactored Helper)
        # This helper should loop through ImagePlanRawData and create ImageBatchTask objects
        generator = ImageAnnotationTaskGenerator(batch)
        created_count = generator.generate_batch_tasks()

        return Response(
            {
                "message": f"Successfully generated {created_count} tasks for Batch {batch.task_name}.",
            },
            status=status.HTTP_201_CREATED,
        )

    # ---------- GET: List Tasks (Manager View) ---------- #
    def get(self, request, *args, **kwargs):
        """
        Lists all tasks for a batch, including their completion status.
        """
        batch_id = kwargs.get("batch") or request.query_params.get("batch")

        if not batch_id:
            return Response(
                {"detail": "batch is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check Batch Access
        try:
            batch = ImagePlan.objects.get(id=batch_id)
        except ImagePlan.DoesNotExist:
            return Response({"detail": "Batch does not exist."}, status=status.HTTP_404_NOT_FOUND)

        if not self.has_access(request.user, batch):
            return Response(
                {"detail": "You do not have permission to view these tasks."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Query the new model: ImageBatchTask
        queryset = ImagePlanTask.objects.filter(batch_id=batch_id).order_by('id')

        # Pagination is handled by ListCreateAPIView standard logic if configured,
        # otherwise we manually serialize.
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)