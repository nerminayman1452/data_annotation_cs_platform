from django.db import models

from apps.tasks.models.task_annotation import BaseTaskAnnotation
from apps.image_annotation.models.plan_task import ImagePlanTask


class ImageTaskAnnotation(BaseTaskAnnotation):
    """
    The concrete link between a Worker and an Image Task,
    containing the results of their work.
    """
    # Link to the specific Image Task
    plan_task = models.ForeignKey(
        ImagePlanTask,
        on_delete=models.CASCADE,
        related_name="annotations" # Easy access: task.annotations.all()
    )

    class Meta:
        # Enforce that one worker is assigned to one image item only once
        unique_together = ('member', 'plan_task')
        verbose_name = "Image Annotation"

    def __str__(self):
        return f"[{self.status}] {self.member} on {self.plan_task}"
