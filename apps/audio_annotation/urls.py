from django.urls import path

from apps.audio_annotation.models.plan_audio_labelling import EmotionLabel
from apps.audio_annotation.views.labelling_types import EmotionLabelView
from apps.audio_annotation.views.plan_audio_Labeling import AudioLabellingPlanView
from apps.audio_annotation.views.plan_audio_segmentation import AudioSegmentationPlanAPIView
from apps.audio_annotation.views.task_audio_segmentation import AudioSegmentationTasksAPIView

urlpatterns = [
    path('create/audio-emotion-label/', EmotionLabelView.as_view(), name='create-text-error-type'),

    path('audio-segmentation-plans/<int:batch_id>/', AudioSegmentationPlanAPIView.as_view(),name='audio-segmentation-plan'),
    path('audio-segmentation-tasks/<int:batch_id>/<int:plan_id>/', AudioSegmentationTasksAPIView.as_view(),
         name='segmentation-task-list-create'),
    path('create/audio-label-plan/<int:batch_id>/', AudioLabellingPlanView.as_view(), name='create-audio-labelling-plan'),
    path('audio-label-plans/<int:batch_id>/', AudioLabellingPlanView.as_view(), name='list-audio-labelling-plans'),
]
