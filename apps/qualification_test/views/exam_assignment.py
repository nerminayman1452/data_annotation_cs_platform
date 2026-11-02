from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.project_management.models.image_plan import ImagePlan
from apps.profile.models.profile import Profile
# from apps.project_management.models.batch import Batchfrom apps.qualification_test.models.exam import ExamBatchMembers
from apps.qualification_test.serializers.assignment import InitialAssignSerializer
from apps.qualification_test.services.exam_assignment import ExamAssignment


class InitialAssignExamTasksAPIView(APIView):
    """
    Initial assignment for all annotators in a batch.
    """

    @extend_schema(
        request=InitialAssignSerializer,
        description="Assigns the initial set of tasks to all annotators in the exam batch.",
        responses={200: dict, 404: dict},
    )
    def post(self, request):
        serializer = InitialAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = self.request.user

        batch_id = serializer.validated_data["batch_id"]
        try:
            batch = ImagePlan.objects.get(id=batch_id)
            #todo profile
            profile = Profile.objects.get(user_id=self.request.user.id)
        except ImagePlan.DoesNotExist:
            return Response({"error": "Batch not found"}, status=status.HTTP_404_NOT_FOUND)
        #todo add exam to batch
        exam_batch = batch.exam
        annotator = ExamBatchMembers.objects.get(profile=profile,exam=exam_batch)
        assignment = ExamAssignment()
        created_annotations = assignment.assign_exam_to_annotator(annotator,exam_batch)

        return Response({
            "message": f"Initial assignment done for exam batch {batch.id}",
            "assigned_count": created_annotations,
        })
