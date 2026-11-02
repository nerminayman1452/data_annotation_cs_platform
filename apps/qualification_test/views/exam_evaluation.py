from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.qualification_test.helper.submit_exam import ExamSubmission
from apps.qualification_test.serializers.exam import ExamSubmissionSerializer


class ExamSubmissionAndEvaluationView(APIView):
    @extend_schema(
        request=None,
        responses={200: dict},
        summary="Submit current user's exam",
        description="Submits and evaluates the current user's active exam attempt for a given exam_id.",
    )
    def post(self, request, exam_id):
        serializer = ExamSubmissionSerializer(
            data=request.data,
            context={'request': request, 'exam_id': exam_id}
        )
        serializer.is_valid(raise_exception=True)

        exam_member = serializer.validated_data['exam_member']

        try:
            ExamSubmission.submit_exam(exam_member.id)
            return Response(
                {"status": "Exam submitted and is now being evaluated."},
                status=status.HTTP_200_OK
            )
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
