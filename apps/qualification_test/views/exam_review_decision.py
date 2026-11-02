from drf_spectacular.utils import extend_schema
from rest_framework import status, generics
from rest_framework.response import Response

from apps.qualification_test.serializers.task_review import ExamTaskReviewDecisionSerializer


class SubmitExamTaskReviewAPIView(generics.GenericAPIView):
    """
    Submit decision for a single exam task review.
    """
    serializer_class = ExamTaskReviewDecisionSerializer

    @extend_schema(
        request=ExamTaskReviewDecisionSerializer,
        responses=ExamTaskReviewDecisionSerializer,
        description=(
                "Submit a review decision.\n"
                "- Reviewer: Accept/Reject (Reject requires reviewed_annotation).\n"
        ),
    )
    def patch(self, request, review_id):
        serializer = self.get_serializer(
            data=request.data,
            context={"request": request, "review_id": review_id}
        )
        serializer.is_valid(raise_exception=True)
        review = serializer.save()
        return Response(self.get_serializer(review).data, status=status.HTTP_200_OK)
