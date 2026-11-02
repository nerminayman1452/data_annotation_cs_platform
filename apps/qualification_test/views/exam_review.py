from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import generics
from rest_framework.pagination import PageNumberPagination

from apps.qualification_test.models.exam import ExamTaskReview
from apps.qualification_test.serializers.task_review import ExamTaskReviewSerializer


class PendingExamTaskReviewPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class PendingExamTaskReviewListView(generics.ListAPIView):
    """
    List all PENDING exam task reviews for the current logged-in reviewer.
    """
    pagination_class = PendingExamTaskReviewPagination
    serializer_class = ExamTaskReviewSerializer

    def get_queryset(self):
        user = self.request.user

        queryset = ExamTaskReview.objects.select_related(
            "task",
            "task__exam",
            "reviewer",
        ).filter(
            reviewer__user_id=user.id,
            decision="PENDING",
        )

        exam_id = self.request.query_params.get("exam_id")
        if exam_id:
            queryset = queryset.filter(task__exam_id=exam_id)

        return queryset.order_by("created_at")

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="exam_id",
                description="Filter pending tasks by exam ID",
                required=False,
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
            ),

        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
