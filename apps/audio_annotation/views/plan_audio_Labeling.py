from django.shortcuts import get_object_or_404
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.audio_annotation.models.plan_audio_labelling import AudioLabellingPlan
from apps.audio_annotation.serializers.plan_audio_labelling import AudioLabellingPlanSerializer
# from apps.text_annotation.models.plan_text_labelling import TextLabellingPlan
# from apps.text_annotation.serializers.plan_text_labelling import TextLabellingPlanSerializer

from apps.project_management.models.batch import Batch

class AudioLabellingPlanView(generics.GenericAPIView):
    """
    POST: Create a new plan from existing batch
    GET: list of created plans for this batch
    """
    serializer_class=AudioLabellingPlanSerializer
    permission_classes = [IsAuthenticated]
    query_set=AudioLabellingPlan.objects.all()

    def post(self, request, batch_id):
        batch = Batch.objects.filter(id=batch_id, created_by=request.user).first()
        if not batch:
            return Response({"detail": "Unauthorized or batch not found."}, status=status.HTTP_403_FORBIDDEN)

        serializer = AudioLabellingPlanSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(batch=batch)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, batch_id):
        # Ensure the batch exists and belongs to the user
        batch = get_object_or_404(Batch, id=batch_id, created_by=request.user)
        plans = AudioLabellingPlan.objects.filter(batch=batch)

        if not plans:
            return Response({"message":"There's no Labelling plans are created yet!"}, status=status.HTTP_404_NOT_FOUND)

        serializer = AudioLabellingPlanSerializer(plans, many=True)

        return Response({"plans": serializer.data}, status=status.HTTP_200_OK)



