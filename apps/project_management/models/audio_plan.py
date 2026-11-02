from django.db import models
# Ensure these imports exist in your project, or comment them out if refactoring tasks later
from django.utils.translation import gettext_lazy as _

from apps.project_management.models.annotation_type import AnnotationType
from apps.project_management.models.plan import BasePlan, BasePlanStatusHistory
from apps.project_management.models.plan_config import BasePlanConfig
from apps.project_management.models.plan_cost import BaseCostConfig
from apps.project_management.models.plan_data import BasePlanRawData
from apps.project_management.models.plan_estimation import BaseEstimationConfig


class AudioPlan(BasePlan):
    # ANNOTATION_TYPES = [
    #     ("SEGMENTATION", "Segmentation"),
    #     ("LABELING", "Labeling"),
    #     ("SPEAKER_DIARIZATION", "Speaker Diarization"),
    #     ("TRANSSCRIPTION", "Transscription"),
    # ]

    annotation_type = models.ForeignKey(
        AnnotationType,
        on_delete=models.PROTECT,
        limit_choices_to={'plan_type': AnnotationType.PlanType.AUDIO},
        related_name='audio_batches',
        verbose_name=_("Annotation Type")
    )  # --- Abstract Hooks ---

    def get_task_model(self):
        pass
        # return AudioAnnotationTask

    def get_annotation_model(self):
        pass
        # return AudioAnnotationSubmission

    def get_raw_unit_count(self):
        pass
        # Assuming relationship name is 'text_tasks' or similar on the Task model
        # Adjust related_name based on your Task definition
        # return self.raw_data_units.count() 

    def get_history_model(self):
        pass
        # return AudioBatchStatusHistory


class AudioPlanStatusHistory(BasePlanStatusHistory):
    plan = models.ForeignKey(
        AudioPlan,
        on_delete=models.CASCADE,
        related_name="status_history"
    )


class EmotionLabel(models.Model):
    emotion_label = models.CharField(max_length=255, verbose_name="Emotion label")

    def __str__(self):
        return self.emotion_label


class SpeakerLabel(models.Model):
    speaker_label = models.CharField(max_length=255, verbose_name="Speaker label")

    def __str__(self):
        return self.speaker_label


class AudioPlanConfig(BasePlanConfig):
    plan = models.OneToOneField(AudioPlan, on_delete=models.CASCADE, related_name="config")
    emotion_labels = models.ManyToManyField(
        EmotionLabel, blank=True, related_name="plan_configs",
        help_text="Select valid labels if this is a Labeling plan"
    )
    speaker_labels = models.ManyToManyField(
        SpeakerLabel, blank=True, related_name="plan_configs",
        help_text="Select valid labels if this is a Labeling plan"
    )
    maximum_segment_duration = models.PositiveIntegerField(
        help_text="Maximum duration (in seconds) for each audio segment. Example: 3600 for 1 hour.",
        default=3600, null=True, blank=True
    )

    def __str__(self):
        return f"{self.id}-Audio Config"


class AudioPlanEstimationConfig(BaseEstimationConfig):
    plan = models.OneToOneField(AudioPlan, on_delete=models.CASCADE, related_name="estimation_config")


class AudioPlanCostConfig(BaseCostConfig):
    plan = models.OneToOneField(AudioPlan, on_delete=models.CASCADE, related_name="cost_config")


class AudioPlanRawData(BasePlanRawData):
    """
    Specific implementation for Audio files (.mp3).
    """
    plan = models.ForeignKey(
        AudioPlan,
        on_delete=models.CASCADE,
        related_name="raw_data_files"
    )

    class Meta:
        verbose_name = "Audio Source File"
        verbose_name_plural = "Audio Source Files"
