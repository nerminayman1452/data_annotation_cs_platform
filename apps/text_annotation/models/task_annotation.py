from django.db import models

from apps.tasks.models.task_annotation import BaseTaskAnnotation
from apps.text_annotation.models.plan_task import TextPlanTask


class TextTaskAnnotation(BaseTaskAnnotation):
    """
    The Link between a Worker and a specific Text Item.
    """
    # Specific link to Text Data
    plan_task = models.ForeignKey(
        TextPlanTask,
        on_delete=models.CASCADE,
        related_name="annotations"
    )

    class Meta:
        # Enforce that one worker is assigned to one text item only once
        unique_together = ('member', 'plan_task')
        verbose_name = "Text Annotation"

    def __str__(self):
        return f"[{self.status}] {self.member} on {self.plan_task}"
