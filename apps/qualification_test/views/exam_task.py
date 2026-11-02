from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import generics, status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from apps.qualification_test.models.exam import ExamTask
from apps.qualification_test.serializers.task import ExamTaskSerializer


class SubmitExamTaskAPIView(generics.GenericAPIView):
    serializer_class = ExamTaskSerializer

    # permission_classes = [permissions.IsAuthenticated]
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="exam_task_id",
                type=int,
                location=OpenApiParameter.PATH,
                description="ID of the annotation to submit"
            )
        ],
        request=ExamTaskSerializer,
        responses=ExamTaskSerializer,
    )
    def patch(self, request, exam_task_id, *args, **kwargs):
        exam_task = get_object_or_404(ExamTask, pk=exam_task_id)
        serializer = self.get_serializer(exam_task, data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
