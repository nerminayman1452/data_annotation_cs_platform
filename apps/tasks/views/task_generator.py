from django.db import transaction
from apps.tasks.serializers.plan_task import GenerateTasksSerializer
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import NotFound, ValidationError

from apps.tasks.helpers.plan_registry import PlanRegistry
from apps.tasks.services.task_generator import PlanTaskGenerationService
from apps.text_annotation.serializers.plan_task import TextPlanTaskSerializer
from apps.image_annotation.serializers.plan_task import ImagePlanTaskSerializer


# Mapping of plan types to their task serializers
TASK_SERIALIZERS = {
    "text": TextPlanTaskSerializer,
    "image": ImagePlanTaskSerializer,
}


class GeneratePlanTasksAPIView(APIView):
    """
    Universal API view for generating tasks for any plan type.
    Accepts plan_id and plan_type in the request body.
    """

    @extend_schema(
        summary="Generate tasks for a plan",
        description=(
            "Generates tasks for a specific plan type. "
            "Supports plan_type: 'text' or 'image'"
        ),
        request=GenerateTasksSerializer,
        responses={
            201: OpenApiResponse(description="Tasks generated successfully"),
            400: OpenApiResponse(description="Invalid plan type or request data"),
            404: OpenApiResponse(description="Plan not found"),
            500: OpenApiResponse(description="Task generation failed"),
        },
    )
    def post(self, request):
        serializer = GenerateTasksSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        plan_id = serializer.validated_data["plan_id"]
        plan_type = serializer.validated_data["plan_type"]

        try:
            plan_model, source_data_builder_class = PlanRegistry.get(plan_type)
        except ValueError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            plan = plan_model.objects.get(id=plan_id)
        except plan_model.DoesNotExist:
            return Response(
                {"detail": f"Plan with id {plan_id} not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            with transaction.atomic():
                service = PlanTaskGenerationService(
                    plan=plan,
                    source_data_builder=source_data_builder_class(),
                )
                created_tasks = service.generate()

        except Exception as e:
            return Response(
                {"detail": f"Task generation failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Serialize the created tasks
        task_serializer_class = TASK_SERIALIZERS.get(plan_type)
        serialized_tasks = task_serializer_class(created_tasks, many=True).data

        return Response(
            {
                "plan_id": plan_id,
                "plan_type": plan_type,
                "tasks_created": len(created_tasks),
                "status": "success",
                "note": (
                    "All files were already processed."
                    if len(created_tasks) == 0
                    else "New tasks generated successfully."
                ),
                "tasks": serialized_tasks,
            },
            status=status.HTTP_201_CREATED,
        )


class PlanTaskListView(APIView):
    """
    List all tasks for a specific plan.
    Supports filtering by plan_id and plan_type.
    """

    @extend_schema(
        summary="List all tasks for a plan",
        description="Retrieve all tasks for a specific plan by plan_id and plan_type",
        responses={
            200: OpenApiResponse(description="Tasks retrieved successfully"),
            400: OpenApiResponse(description="Invalid plan type"),
            404: OpenApiResponse(description="Plan not found"),
        },
    )
    def get(self, request, plan_id, plan_type):
        """List all tasks for a plan"""
        try:
            plan_model, _ = PlanRegistry.get(plan_type)
        except ValueError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            plan = plan_model.objects.get(id=plan_id)
        except plan_model.DoesNotExist:
            return Response(
                {"detail": f"Plan with id {plan_id} not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        task_model = plan.get_task_model()
        tasks = task_model.objects.filter(plan=plan)

        task_serializer_class = TASK_SERIALIZERS.get(plan_type)
        serialized_tasks = task_serializer_class(tasks, many=True).data

        return Response(
            {
                "plan_id": plan_id,
                "plan_type": plan_type,
                "total_tasks": tasks.count(),
                "tasks": serialized_tasks,
            },
            status=status.HTTP_200_OK,
        )


class PlanTaskDetailView(APIView):
    """
    Retrieve, update, or delete a specific task for a plan.
    """

    def get_plan_and_task(self, plan_id, plan_type, task_id):
        """Helper method to get plan and task"""
        try:
            plan_model, _ = PlanRegistry.get(plan_type)
        except ValueError as e:
            raise ValidationError(str(e))

        try:
            plan = plan_model.objects.get(id=plan_id)
        except plan_model.DoesNotExist:
            raise NotFound(f"Plan with id {plan_id} not found")

        task_model = plan.get_task_model()
        try:
            task = task_model.objects.get(id=task_id, plan=plan)
        except task_model.DoesNotExist:
            raise NotFound(f"Task with id {task_id} not found for this plan")

        return plan, task, task_model

    @extend_schema(
        summary="Retrieve a specific task",
        description="Get details of a specific task by task_id",
        responses={
            200: OpenApiResponse(description="Task retrieved successfully"),
            400: OpenApiResponse(description="Invalid plan type"),
            404: OpenApiResponse(description="Plan or task not found"),
        },
    )
    def get(self, request, plan_id, plan_type, task_id):
        """Retrieve a specific task"""
        try:
            plan, task, _ = self.get_plan_and_task(plan_id, plan_type, task_id)
        except (ValidationError, NotFound) as e:
            status_code = status.HTTP_400_BAD_REQUEST if isinstance(e, ValidationError) else status.HTTP_404_NOT_FOUND
            return Response(
                {"detail": str(e.detail)},
                status=status_code,
            )

        task_serializer_class = TASK_SERIALIZERS.get(plan_type)
        serialized_task = task_serializer_class(task).data

        return Response(serialized_task, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Update a specific task",
        description="Update details of a specific task",
        responses={
            200: OpenApiResponse(description="Task updated successfully"),
            400: OpenApiResponse(description="Invalid plan type or request data"),
            404: OpenApiResponse(description="Plan or task not found"),
        },
    )
    def put(self, request, plan_id, plan_type, task_id):
        """Update a specific task"""
        try:
            plan, task, task_model = self.get_plan_and_task(plan_id, plan_type, task_id)
        except (ValidationError, NotFound) as e:
            status_code = status.HTTP_400_BAD_REQUEST if isinstance(e, ValidationError) else status.HTTP_404_NOT_FOUND
            return Response(
                {"detail": str(e.detail)},
                status=status_code,
            )

        task_serializer_class = TASK_SERIALIZERS.get(plan_type)
        serializer = task_serializer_class(task, data=request.data, partial=True)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Delete a specific task",
        description="Delete a specific task by task_id",
        responses={
            204: OpenApiResponse(description="Task deleted successfully"),
            400: OpenApiResponse(description="Invalid plan type"),
            404: OpenApiResponse(description="Plan or task not found"),
        },
    )
    def delete(self, request, plan_id, plan_type, task_id):
        """Delete a specific task"""
        try:
            plan, task, task_model = self.get_plan_and_task(plan_id, plan_type, task_id)
        except (ValidationError, NotFound) as e:
            status_code = status.HTTP_400_BAD_REQUEST if isinstance(e, ValidationError) else status.HTTP_404_NOT_FOUND
            return Response(
                {"detail": str(e.detail)},
                status=status_code,
            )

        task.delete()
        return Response(
            {"detail": f"Task {task_id} deleted successfully"},
            status=status.HTTP_204_NO_CONTENT,
        )
