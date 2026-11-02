from django.db import models

from apps.project_management.models.plan_members import PlanMember
from apps.project_management.models.time_stamp import TimeStampedModel


class BaseTaskAnnotation(TimeStampedModel):
    """
    MERGED MODEL:
    Represents the lifecycle of a worker working on a specific task.
    Combines the 'Assignment' (Who) and the 'Submission' (Result).
    """
    STATUS_CHOICES = [
        ("ASSIGNED", "Assigned"),  # Worker has the task, hasn't started
        ("IN_PROGRESS", "In Progress"),  # Worker opened the editor
        ("SKIPPED", "Skipped"),  # Worker skipped this task
        ("SUBMITTED", "Submitted"),  # Ready for review
        ("ACCEPTED", "Accepted"),  # Approved by QA/Reviewer
        ("REJECTED", "Rejected"),  # Sent back to annotator
    ]

    # --- Assignment Fields ---
    member = models.ForeignKey(
        PlanMember,
        on_delete=models.CASCADE,
        related_name="%(class)s_history"
    )

    # --- Submission/Result Fields ---
    spent_time = models.IntegerField(default=0, help_text="Time spent in seconds")

    # We allow null=True now because when first ASSIGNED, data is empty
    annotated_data = models.JSONField(
        null=True,
        blank=True,
        default=dict,
        help_text="The actual label/result payload"
    )

    status = models.CharField(
        choices=STATUS_CHOICES, default="ASSIGNED", max_length=32
    )

    class Meta:
        abstract = True