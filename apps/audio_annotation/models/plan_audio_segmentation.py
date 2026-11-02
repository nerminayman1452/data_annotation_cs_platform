from django.db import models

from apps.project_management.models.image_plan import ImagePlan


class AudioSegmentationPlan(models.Model):
    plan_name = models.CharField(max_length=255)
    batch = models.ForeignKey(ImagePlan, on_delete=models.CASCADE, null=True)
    maximum_segment_duration = models.PositiveIntegerField(
        help_text="Maximum duration (in seconds) for each audio segment. Example: 3600 for 1 hour.",
        default=3600
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.plan_name
