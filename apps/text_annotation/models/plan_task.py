from django.db import models

from apps.tasks.models.plan_task import BasePlanTask
from apps.project_management.models.plan_members import PlanMember


class TextPlanTask(BasePlanTask):
    """
    Specific implementation for Text.
    Manages one sentence from 'TextPlanRawData' within a 'TextPlan'.
    """
    # Link to the Parent Batch
    plan = models.ForeignKey(
        'project_management.TextPlan',
        on_delete=models.CASCADE,
        related_name="plan_tasks"  # Matches AbstractBatch.get_raw_count() logic
    )

    # Link to the specific Raw Data File
    plan_file = models.ForeignKey(
        'project_management.TextPlanRawData',
        on_delete=models.CASCADE,
        related_name="raw_data_tasks"
    )

    # The Worker Pool for this specific task
    members = models.ManyToManyField(
        PlanMember,
        through='text_annotation.TextTaskAnnotation',
        related_name='assigned_text_tasks',
    )

    def __str__(self):
        return f"Item {self.id} in {self.plan.name} "

