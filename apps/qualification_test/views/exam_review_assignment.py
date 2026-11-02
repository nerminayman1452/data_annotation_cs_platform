from drf_spectacular.utils import extend_schema
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from apps.qualification_test.serializers.task_review import AssignExamReviewerSerializer
from apps.qualification_test.services.exam_review import ExamTaskReviewService


class AssignExamReviewerAPIView(APIView):
    # permission_classes = [permissions.IsAuthenticated]

    @extend_schema(

        description=(
            "Assign all exam tasks belonging to an annotator (ExamReviewBatchMember) "
            "to a reviewer (batch owner or reviewer/super-reviewer)."
        ),
        request=AssignExamReviewerSerializer,

    )
    def post(self, request):
        serializer = AssignExamReviewerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        exam_member = serializer.validated_data["exam_member"]
        reviewer = serializer.validated_data["reviewer"]
        batch = serializer.validated_data["batch"]

        assigned_reviews = ExamTaskReviewService.assign_reviewer_to_annotator_tasks(
            annotator_exam_member=exam_member,
            reviewer=reviewer,
            batch=batch
        )

        return Response(
            {
                "message": f"Reviewer assigned to {len(assigned_reviews)} exam tasks successfully.",
                "annotator_id": exam_member.profile.id,
                "reviewer_id": reviewer.id,
                "batch_id": batch.id,
                "total_assigned_tasks": len(assigned_reviews),
            },
            status=status.HTTP_200_OK,
        )