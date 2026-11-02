from django.db import models
from apps.project_management.models.plan_members import PlanMember
from apps.text_annotation.models.task_text_segmentation import TextSegmentationTaskResult
# from apps.project_management.models import BatchMembers


class ReviewTextSegmentationResult(models.Model):
    STATUS_CHOICES = [
        ("in_progress", "In Progress"),
        ("submitted", "Submitted"),
        ("skipped", "Skipped"),
    ]
    reviewer = models.ForeignKey(
        PlanMember, on_delete=models.CASCADE, verbose_name="Reviewer", null=True, blank=True
    )
    task = models.ForeignKey(
      TextSegmentationTaskResult, on_delete=models.CASCADE, verbose_name="Text Segmentation Task"
    )
    feedback = models.TextField(verbose_name="Reviewer Feedback", blank=True, null=True)
    role = models.CharField(max_length=50, help_text="Reviewer role (e.g., linguistic_lead)")
    is_accepted = models.BooleanField(
        default=True, verbose_name="is accepted", help_text="is the review result accepted"
    )
    status = models.CharField(
        max_length=45, choices=STATUS_CHOICES, default="in_progress", verbose_name="Status"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Review by {self.reviewer} - {self.is_accepted}"
