from rest_framework.generics import ListCreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from unused_scripts.image_task_generator import ImageAnnotationTaskGenerator
from apps.project_management.models.batch import Batch


# from apps.project_management.models.batch import Batchfrom apps.image_annotation.helpers.task_generator import ImageAnnotationTaskGenerator


class BaseImageTasksAPIView(ListCreateAPIView):
    """
    Base API for image annotation task generation & listing
    """

    permission_classes = [IsAuthenticated]

    # must be defined by subclasses
    plan_model = None
    task_model = None
    serializer_class = None
    plan_config_model = None  # optional

    def has_access(self, user, batch):
        return batch.created_by == int(user.id)

    # ---------- POST: generate tasks ---------- #

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)

        batch = serializer.validated_data["batch"]
        plan = serializer.validated_data["plan"]

        if not self.has_access(request.user, batch):
            return Response(
                {"detail": "You do not have permission to create tasks for this batch."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # optional plan config validation
        if self.plan_config_model:
            self.plan_config_model.objects.get(id=plan.plan_config_id)

        generator = ImageAnnotationTaskGenerator(plan)
        created_tasks = generator.generate_tasks()

        response_serializer = self.get_serializer(created_tasks, many=True)
        return Response(
            {
                "message": f"Successfully created {len(created_tasks)} tasks.",
                "tasks": response_serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )

    # ---------- GET: list tasks ---------- #

    def get(self, request, *args, **kwargs):
        batch_id = kwargs.get("batch_id")
        plan_id = kwargs.get("plan_id")

        if not batch_id or not plan_id:
            return Response(
                {"detail": "batch_id and plan_id are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            batch = Batch.objects.get(id=batch_id)
            plan = self.plan_model.objects.get(id=plan_id, batch=batch)
        except (Batch.DoesNotExist, self.plan_model.DoesNotExist):
            return Response(
                {"detail": "Batch or Plan does not exist."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not self.has_access(request.user, batch):
            return Response(
                {"detail": "You do not have permission to view these tasks."},
                status=status.HTTP_403_FORBIDDEN,
            )

        queryset = self.task_model.objects.filter(
            batch_data__batch_id=batch_id,
            plan_id=plan_id,
        )

        if not queryset.exists():
            return Response(
                {"message": "No tasks generated yet."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
