import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.project_management.models.annotation_type import AnnotationType
from apps.project_management.models.plan_config import BasePlanConfig
from apps.project_management.models.plan_cost import BaseCostConfig
from apps.project_management.models.plan_data import BasePlanRawData
from apps.project_management.models.plan_estimation import BaseEstimationConfig
from apps.project_management.models.plan import BasePlan, BasePlanStatusHistory
from apps.text_annotation.models import TextPlanTask
from apps.text_annotation.models.task_annotation import TextTaskAnnotation


class TextPlan(BasePlan):
    # id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    id = models.BigIntegerField(primary_key=True, editable=False, default=BasePlan.generate_unique_int_id)

    
    ANNOTATION_TYPES = [
        ("SEGMENTATION", "Segmentation"),
        ("LABELING", "Labeling"),
        ("SUMMARIZATION", "Summarization"),
        ("VALIDATION", "Validation"),
    ]

    annotation_type = models.ForeignKey(
        AnnotationType,
        on_delete=models.PROTECT,  # Prevent deleting the type if batches use it
        limit_choices_to={'plan_type': AnnotationType.PlanType.TEXT},
        related_name='text_batches',
        verbose_name=_("Annotation Type")
    )
    
    class Meta:
        # Keep the same db_table name to avoid migration issues
        db_table = 'project_management_textplan'
    # --- Abstract Hooks ---
    def get_task_model(self):
        # The unit of work (The Sentence)
        return TextPlanTask

    def get_annotation_model(self):
        # The link between User <-> Sentence (The Work)
        return TextTaskAnnotation

    def get_raw_unit_count(self):
        # Assuming relationship name is 'text_tasks' or similar on the Task model
        # Adjust related_name based on your Task definition
        return self.raw_data_files.count()

    def get_history_model(self):
        return TextPlanStatusHistory
    
    def get_config(self):
        # Assumes you define the OneToOneField with related_name='config'
        return self.config 

    def get_cost_config(self):
        # Assumes related_name='cost_config'
        return self.cost_config

    def get_estimation_config(self):
        # Assumes related_name='estimation_config'
        return self.estimation_config

class TextPlanStatusHistory(BasePlanStatusHistory):
    plan = models.ForeignKey(
        TextPlan,
        on_delete=models.CASCADE,
        related_name="status_history"
    )


# --- Label & Type Models ---

class TextSentenceType(models.Model):
    sentence_type = models.CharField(max_length=255, verbose_name="Sentence Type")

    def __str__(self):
        return self.sentence_type


class TextLabelType(models.Model):
    label_type = models.CharField(max_length=255, verbose_name="Label Type")

    def __str__(self):
        return self.label_type


class TextErrorType(models.Model):
    error_type = models.CharField(max_length=255, verbose_name="Error Type")

    def __str__(self):
        return self.error_type


class TextValidationType(models.Model):
    validation_type = models.CharField(max_length=255, verbose_name="Validation Type")

    def __str__(self):
        return self.validation_type


class TextSplitter(models.Model):
    splitter = models.CharField(
        max_length=50, 
        default="\n", 
        help_text="Character or Regex used to split text"
    )

    def __str__(self):
        return f"'{self.splitter}'"


# --- Config Models ---

class TextPlanConfig(BasePlanConfig):
    plan = models.OneToOneField(TextPlan, on_delete=models.CASCADE, related_name="config")
    
    # Labeling Configuration
    allowed_labels = models.ManyToManyField(
        TextLabelType, blank=True,null=True, related_name="plan_configs",
        help_text="Select valid labels if this is a Labeling plan"
    )
    allowed_errors = models.ManyToManyField(
        TextErrorType, blank=True,null=True,  related_name="plan_configs",
        help_text="Select valid error types if this is a Labeling plan"
    )
    allowed_sentence_types = models.ManyToManyField(
        TextSentenceType, blank=True, null=True, related_name="plan_configs"
    )

    # Validation Configuration
    allowed_validation_types = models.ManyToManyField(
        TextValidationType, blank=True, null=True,  related_name="plan_configs",
        help_text="Select validation criteria if this is a Validation plan"
    )

    # Summarization Configuration
    max_summary_length = models.IntegerField(null=True, blank=True)
    min_summary_length = models.IntegerField(null=True, blank=True)

    # Segmentation Configuration
    segmentation_splitter = models.ForeignKey(
        TextSplitter,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.id}-Text Config"


class TextPlanEstimationConfig(BaseEstimationConfig):
    plan = models.OneToOneField(TextPlan, on_delete=models.CASCADE, related_name="estimation_config")


class TextPlanCostConfig(BaseCostConfig):
    plan = models.OneToOneField(TextPlan, on_delete=models.CASCADE, related_name="cost_config")


class TextPlanRawData(BasePlanRawData):
    """
    Specific implementation for Text files (CSV, TXT, JSON).
    """
    plan = models.ForeignKey(
        TextPlan,
        on_delete=models.CASCADE,
        related_name="raw_data_files"
    )

    class Meta:
        verbose_name = "Text Source File"
        verbose_name_plural = "Text Source Files"