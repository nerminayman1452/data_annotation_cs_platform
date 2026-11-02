from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.audio_annotation.models.plan_audio_segmentation import AudioSegmentationPlan
from apps.audio_annotation.serializers.plan_audio_segmentation import AudioSegmentationPlanSerializer


class AudioSegmentationPlanAPIView(GenericAPIView):
    serializer_class = AudioSegmentationPlanSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        batch_id = self.kwargs.get('batch_id')
        return AudioSegmentationPlan.objects.filter(batch_id=batch_id, batch_id__created_by=self.request.user)

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        batch_id = self.kwargs.get('batch_id')
        request.data['batch'] = batch_id

        serializer = self.get_serializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
