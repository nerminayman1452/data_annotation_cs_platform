from django.db import models

from apps.tasks.models.plan_task import BasePlanTask
from apps.project_management.models.plan_members import PlanMember
from apps.project_management.models.audio_plan import AudioPlan, AudioPlanRawData


class AudioPlanTask(BasePlanTask):
    """
    Specific implementation for Audio.
    """
    plan = models.ForeignKey(
        AudioPlan,
        on_delete=models.CASCADE,
        related_name="plan_tasks"
    )

    plan_file = models.ForeignKey(
        AudioPlanRawData,
        on_delete=models.CASCADE,
        related_name="raw_data_tasks"
    )

    # UPDATED: Through model is now the merged Annotation model
    members = models.ManyToManyField(
        PlanMember,
        through='audio_annotation.AudioTaskAnnotation',
        related_name='assigned_audio_tasks',
    )

    def __str__(self):
        return f"Item {self.id} in {self.plan}"