from django.contrib import admin

from apps.audio_annotation.models.plan_audio_labelling import AudioLabellingPlan, EmotionLabel
from apps.audio_annotation.models.plan_audio_segmentation import AudioSegmentationPlan
from apps.audio_annotation.models.plan_audio_speaker_diarization import AudioSpeakerDiarizationPlan, SpeakerLabel
from apps.audio_annotation.models.plan_audio_transcription import AudioTranscriptionPlan
from apps.audio_annotation.models.task_audio_segmentation import AudioSegmentationTaskResult

# Register your models here.
admin.site.register(EmotionLabel)
admin.site.register(SpeakerLabel)

admin.site.register(AudioSegmentationPlan)
admin.site.register(AudioSpeakerDiarizationPlan)
admin.site.register(AudioLabellingPlan)
admin.site.register(AudioTranscriptionPlan)

admin.site.register(AudioSegmentationTaskResult)
