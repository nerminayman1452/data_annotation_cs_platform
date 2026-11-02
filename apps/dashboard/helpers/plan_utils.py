from datetime import timedelta, datetime, timezone
from typing import List, Optional, Tuple

# from apps.image_annotation.models.plan_img_classification import ImageClassificationPlan
# from apps.image_annotation.models.plan_img_object_detection import ObjectDetectionPlan
# from apps.image_annotation.models.plan_img_polygons import PolygonPlan
# from apps.image_annotation.models.task_img_classification import ImageClassificationTask, ImageClassificationAnnotation
# from apps.image_annotation.models.task_img_object_detection import ObjectDetectionTask, ObjectDetectionAnnotation
# from apps.image_annotation.models.task_img_polygons import PolygonTask, PolygonAnnotation
# from apps.text_annotation.models.plan_text_labelling import TextLabellingPlan
# from apps.text_annotation.models.plan_text_summarization import TextSummarizationPlan
# from apps.text_annotation.models.plan_text_validation import TextValidationPlan
# from apps.text_annotation.models.plan_text_segmentation import TextSegmentationPlan
from apps.audio_annotation.models.plan_audio_labelling import AudioLabellingPlan
from apps.audio_annotation.models.plan_audio_segmentation import AudioSegmentationPlan
from apps.audio_annotation.models.plan_audio_transcription import AudioTranscriptionPlan
from apps.audio_annotation.models.plan_audio_speaker_diarization import AudioSpeakerDiarizationPlan


class PlanInspector:
    """
    Provides:
    - centralized list of plan/task/annotation model tuples
    - counting helpers
    - deadline calculation
    - days-remaining computation (timezone-aware)
    """

    PLAN_MODELS: List[Tuple] = [
        # ImageClassificationPlan,
        # (None, ImageClassificationTask, ImageClassificationAnnotation),
        # (ObjectDetectionPlan, ObjectDetectionTask, ObjectDetectionAnnotation),
        # (PolygonPlan, PolygonTask, PolygonAnnotation),
        # (TextLabellingPlan, None, None),
        # (TextSummarizationPlan, None, None),
        # (TextValidationPlan, None, None),
        # (TextSegmentationPlan, None, None),
        (AudioLabellingPlan, None, None),
        (AudioSegmentationPlan, None, None),
        (AudioTranscriptionPlan, None, None),
        (AudioSpeakerDiarizationPlan, None, None),
    ]

    @classmethod
    def get_plan_models(cls):
        return cls.PLAN_MODELS

    @staticmethod
    def count_tasks_and_completed(plan, task_model, annotation_model) -> Tuple[int, int]:
        tasks_count = 0
        completed_count = 0
        try:
            if task_model is not None:
                tasks_count = task_model.objects.filter(plan=plan).count()
            if annotation_model is not None:
                completed_count = annotation_model.objects.filter(task__plan=plan, status="submitted").count()
        except Exception:
            tasks_count = getattr(plan, "tasks_count", 0) or 0
            completed_count = getattr(plan, "completed_count", 0) or 0
        return tasks_count, completed_count

    @staticmethod
    def get_plan_duration(plan) -> Optional[int]:
        try:
            if hasattr(plan, "plan_config") and plan.plan_config:
                return getattr(plan.plan_config, "duration", None)
            return getattr(plan, "duration", None)
        except Exception:
            return None

    @staticmethod
    def calculate_deadline(plan, duration: Optional[int]):
        if not duration or not getattr(plan, "created_at", None):
            return None
        try:
            return plan.created_at + timedelta(days=duration)
        except Exception:
            return None

    @staticmethod
    def days_remaining(deadline: Optional[datetime], now: Optional[datetime] = None) -> Optional[int]:
        if not deadline:
            return None
        try:
            # If no 'now' provided, compute using deadline's tzinfo if available
            if now is None:
                if deadline.tzinfo is not None:
                    now = datetime.now(deadline.tzinfo)
                else:
                    now = datetime.utcnow().replace(tzinfo=timezone.utc)
            delta = deadline - now
            # if deadline in future, return full days remaining; otherwise 0
            return max(0, delta.days) if delta.total_seconds() > 0 else 0
        except Exception:
            return None


# convenience functional wrappers for easier use in procedural code
get_plan_models = PlanInspector.get_plan_models
count_tasks_and_completed = PlanInspector.count_tasks_and_completed
get_plan_duration = PlanInspector.get_plan_duration
calculate_deadline = PlanInspector.calculate_deadline
days_remaining = PlanInspector.days_remaining
