from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from rest_framework import viewsets, permissions, filters

from apps.qualification_test.models.exam import ExamBatchMembers
from apps.qualification_test.serializers.members import ExamBatchMembersSerializer


class ExamReviewBatchMembersViewSet(viewsets.ModelViewSet):
    """
    API endpoint to view or manage exam review batch members.
    """

    queryset = ExamBatchMembers.objects.select_related('profile', 'exam', 'batch')
    serializer_class = ExamBatchMembersSerializer
    # permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="exam",
                description="Filter by exam ID",
                required=False,
                type=int,
            ),
            OpenApiParameter(
                name="batch",
                description="Filter by batch ID",
                required=False,
                type=int,
            ),
        ],
        responses={
            200: OpenApiResponse(
                response=ExamBatchMembersSerializer,
                description="List of exam review batch members."
            )
        },
        examples=[],
    )
    def list(self, request, *args, **kwargs):
        """Retrieve a list of exam review batch members, optionally filtered by exam or batch."""
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        """
        Optionally filter by exam ID or batch ID.
        """
        queryset = super().get_queryset()
        exam_id = self.request.query_params.get('exam')
        batch_id = self.request.query_params.get('batch')

        if exam_id:
            queryset = queryset.filter(exam_id=exam_id)
        if batch_id:
            queryset = queryset.filter(batch_id=batch_id)

        return queryset