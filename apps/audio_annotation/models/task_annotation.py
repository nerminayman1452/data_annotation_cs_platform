from django.db import models

from apps.tasks.models.task_annotation import BaseTaskAnnotation
from apps.audio_annotation.models.plan_task import AudioPlanTask


class AudioTaskAnnotation(BaseTaskAnnotation):
    """
    The concrete link between a Worker and an Audio Task,
    containing the results of their work.
    """
    # Link to the specific Audio Task
    plan_task = models.ForeignKey(
        AudioPlanTask,
        on_delete=models.CASCADE,
        related_name="annotations" # Easy access: task.annotations.all()
    )

    class Meta:
        # Enforce that one worker is assigned to one audio item only once
        unique_together = ('member', 'plan_task')
        verbose_name = "Audio Annotation"

    def __str__(self):
        return f"[{self.status}] {self.member} on {self.plan_task}"
