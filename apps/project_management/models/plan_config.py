from django.db import models

from apps.project_management.models.time_stamp import TimeStampedModel


class BasePlanConfig(TimeStampedModel):
    #todo discuss with salah (if needed the limited num of workers who will enter the plan)
    """Operational Rules"""
    # config={"guideline:"" , add any other config}
    config = models.JSONField(null=True, default=dict)
    workers_per_task = models.PositiveIntegerField(default=1)
    task_distribution_mode = models.CharField(
        max_length=50, choices=[("auto", "Automatic"), ("manual", "Manual")], default="auto"
    )
    # is_auto_review = models.BooleanField(default=False)
    standard = models.PositiveIntegerField(default=15)
    time_per_task = models.PositiveIntegerField(default=30)
    acceptance_agreement = models.IntegerField(null=True, blank=True)
    #todo reviewer percentage && super-reviewer percentagein case of review approach

    class Meta:
        abstract = True
