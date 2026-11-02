import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.image_annotation.models import ImagePlanTask
from apps.image_annotation.models.task_annotation import ImageTaskAnnotation
from apps.project_management.models.annotation_type import AnnotationType
from apps.project_management.models.plan import BasePlan, BasePlanStatusHistory
from apps.project_management.models.plan_config import BasePlanConfig
from apps.project_management.models.plan_cost import BaseCostConfig
from apps.project_management.models.plan_data import BasePlanRawData
from apps.project_management.models.plan_estimation import BaseEstimationConfig


class ImagePlan(BasePlan):
    # id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    id = models.BigIntegerField(primary_key=True, editable=False,default=BasePlan.generate_unique_int_id)
    
    ANNOTATION_TYPES = [
        ("CLASSIFICATION", "Classification"),
        ("OBJECT_DETECTION", "Object Detection"),
        ("POLYGONS", "Polygons"),
    ]

    annotation_type = models.ForeignKey(
        AnnotationType,
        on_delete=models.PROTECT,
        limit_choices_to={'plan_type': AnnotationType.PlanType.IMAGE},
        related_name='image_batches',
        verbose_name=_("Annotation Type")
    )
    
    class Meta:
        # Keep the same db_table name to avoid migration issues
        db_table = 'project_management_imageplan'

    def get_task_model(self):
        return ImagePlanTask

    def get_annotation_model(self):
        return ImageTaskAnnotation

    def get_raw_unit_count(self):
        # Assumes you have a TextDataUnit or TextTask model linked
        # return self.image_tasks.count()
        return self.raw_data_files.count()

    def get_history_model(self):
        return ImagePlanStatusHistory

    def get_cost_config(self):
        return self.cost_config

    def get_config(self):
        return self.config

    def get_estimation_config(self):
        try:
            return self.estimation_config
        except ImagePlanEstimationConfig.DoesNotExist:
            return None

    # def total_workforce(self):
    #     return self.annotator_workforce() + self.reviewer_workforce()


class ImagePlanStatusHistory(BasePlanStatusHistory):
    plan = models.ForeignKey(
        ImagePlan,
        on_delete=models.CASCADE,
        related_name="status_history"
    )


class ImageLabelType(models.Model):
    label_type = models.CharField(max_length=255, verbose_name="Classification Image Label Type")

    def __str__(self):
        return self.label_type


class DetectionLabelType(models.Model):
    label_type = models.CharField(max_length=255, verbose_name="Object Type")

    def __str__(self):
        return self.label_type


class PolygonLabelType(models.Model):
    label_type = models.CharField(max_length=255, verbose_name="Polygon Label Type")

    def __str__(self):
        return self.label_type


class ImagePlanConfig(BasePlanConfig):
    plan = models.OneToOneField(ImagePlan, on_delete=models.CASCADE, related_name="config")
    classification_labels = models.ManyToManyField(
        ImageLabelType, blank=True, null=True, related_name="plan_configs",
        help_text="Select valid labels if this is a Labeling plan"
    )
    detection_labels = models.ManyToManyField(
        DetectionLabelType, blank=True,null=True, related_name="plan_configs",
        help_text="Select valid labels if this is a Labeling plan"
    )
    polygon_labels = models.ManyToManyField(
        PolygonLabelType, blank=True,null=True, related_name="plan_configs",
        help_text="Select valid labels if this is a Labeling plan"
    )

    def __str__(self):
        return f"{self.id}-Image Config"


class ImagePlanEstimationConfig(BaseEstimationConfig):
    plan = models.OneToOneField(ImagePlan, on_delete=models.CASCADE, related_name="estimation_config")


class ImagePlanCostConfig(BaseCostConfig):
    plan = models.OneToOneField(ImagePlan, on_delete=models.CASCADE, related_name="cost_config")


class ImagePlanRawData(BasePlanRawData):
    """
     Specific implementation for Image files (png, jpeg).
     """
    plan = models.ForeignKey(
        ImagePlan,
        on_delete=models.CASCADE,
        related_name="raw_data_files"
    )

    class Meta:
        verbose_name = "Image Source File"
        verbose_name_plural = "Image Source Files"
