from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from apps.audio_annotation.models.plan_audio_labelling import EmotionLabel
from apps.audio_annotation.serializers.plan_audio_labelling import EmotionLabelSerializer


class EmotionLabelView(generics.ListCreateAPIView):
    serializer_class = EmotionLabelSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    query_set = EmotionLabel.objects.all()
