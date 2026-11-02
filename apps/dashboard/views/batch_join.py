from apps.dashboard.models.batch_join import BatchJoinRequest
from apps.helpers.profile_info import ProfileInfoHelper
from apps.project_management.models.batch import Batch
from apps.project_management.models.plan_members import PlanMember
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from apps.dashboard.helpers.batch_access_manager import BatchAccessManager
from apps.dashboard.serializers.batch_request import BatchJoinRequestSerializer

class RequestBatchAccessAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, batch_id):
        user = request.user
        profile_id = ProfileInfoHelper.get_profile_id_from_request(request)
        try:
            batch = Batch.objects.get(id=batch_id)
        except Batch.DoesNotExist:
            return Response({"detail": "Batch not found."}, status=status.HTTP_404_NOT_FOUND)

        if BatchAccessManager.can_access_batch(batch, profile_id):
            return Response({"detail": "You can already access this batch."}, status=status.HTTP_200_OK)

        try:
            join_request = BatchAccessManager.request_access(request,batch, user.id)
        except Exception as e:
            return Response({"detail": f"Error creating join request: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        serializer = BatchJoinRequestSerializer(join_request)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ApproveBatchAccessAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, request_id):
        user = request.user
        try:
            join_request = BatchJoinRequest.objects.select_related("batch").get(id=request_id)
        except BatchJoinRequest.DoesNotExist:
            return Response({"detail": "Join request not found."}, status=status.HTTP_404_NOT_FOUND)

        # Only batch creator can approve
        if join_request.batch.created_by != user.id:
            return Response({"detail": "Not authorized."}, status=status.HTTP_403_FORBIDDEN)

        join_request.status = "approved"
        join_request.save()

        # Add the annotator to BatchMembers automatically
        PlanMember.objects.get_or_create(batch=join_request.batch, profile=join_request.annotator, defaults={"user_role": "annotator"})

        return Response({"detail": "Access approved successfully."}, status=status.HTTP_200_OK)
    
    def get(self, request, request_id):
        user = request.user
        try:
            join_request = BatchJoinRequest.objects.select_related("batch").get(id=request_id)
        except BatchJoinRequest.DoesNotExist:
            return Response({"detail": "Join request not found."}, status=status.HTTP_404_NOT_FOUND)

        # Only batch creator can view
        if join_request.batch.created_by != user.id:
            return Response({"detail": "Not authorized."}, status=status.HTTP_403_FORBIDDEN)

        serializer = BatchJoinRequestSerializer(join_request, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class ListBatchJoinRequestsAPIView(APIView):
    """
    Allows batch creators or admins to see join requests for their batches.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # Filter requests for batches created by this user
        join_requests = BatchJoinRequest.objects.filter(
            batch__created_by=user.id
        ).select_related("batch").order_by("-created_at")

        serializer = BatchJoinRequestSerializer(join_requests, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
