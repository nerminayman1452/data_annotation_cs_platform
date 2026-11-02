from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

# from apps.project_management.models.batch import Batchfrom apps.project_management.models.image_batch import ImageBatch
from apps.qualification_test.models.exam import ExamBatchMembers, ExamTask
from apps.qualification_test.serializers.exam import ExamSerializer
from apps.qualification_test.serializers.task import ExamTaskSerializer


class AnnotatorExamTaskListView(generics.GenericAPIView):
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="batch_id",
                description="Filter questions by batch ID (required)",
                required=True,
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
            ),
        ]
    )
    def get(self, request, *args, **kwargs):
        user = request.user
        batch_id = request.query_params.get("batch_id")

        if not batch_id:
            raise ValidationError({"batch_id": "This parameter is required."})

        batch = ImageBatch.objects.get(id=batch_id)
        exam = batch.exam

        try:
            annotator = ExamBatchMembers.objects.get(
                profile__user_id=user.id,
                exam=exam
            )
        except ExamBatchMembers.DoesNotExist:
            raise ValidationError("Profile not found for the current user.")

        if not annotator.can_open_exam:
            raise ValidationError("This exam has already been submitted or cannot be opened.")

        # Fetch all tasks for this annotator and exam
        tasks = ExamTask.objects.select_related("question").filter(
            annotator=annotator,
            exam=exam
        ).order_by("id")

        # Serialize exam once
        exam_data = ExamSerializer(exam, context={"request": request}).data
        tasks_data = ExamTaskSerializer(tasks, many=True, context={"request": request}).data

        return Response({
            "exam": exam_data,
            "tasks": tasks_data
        })