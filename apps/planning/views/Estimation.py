from apps.planning.services.Estimation_service import BatchEstimationService
from apps.project_management.models.batch import Batch
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response 
from rest_framework.views import APIView   


class BatchEstimationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, batch_id):
        batch_exists = Batch.objects.filter(id=int(batch_id)).exists()
        if not batch_exists:
            return Response({"error": "Batch not found."}, status=404)
        data = BatchEstimationService.get_batch_estimations(batch_id)
        if not data:
            data = {}
        return Response(data)

# class ProjectEstimationView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request, project_id):
#         data = ProjectEstimationService.get_project_estimations(project_id)
#         return Response(data)
    
# class ApprovalEstimationView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request, batch_id):
#         data = BatchEstimationService.get_approval_estimations(batch_id)
#         return Response(data)