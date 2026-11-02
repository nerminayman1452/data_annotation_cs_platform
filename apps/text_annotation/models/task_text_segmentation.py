from django.db import models
from django.utils.timezone import now

from apps.project_management.models.plan_members import PlanMember
from apps.project_management.models.text_plan import TextPlan
from apps.project_management.models.text_plan import TextPlanRawData
# from apps.text_annotation.models.plan_text_segmentation import TextSegmentationPlan
from apps.project_management.models import Batch
from apps.text_annotation.models.qualification_config import WorkerQualification


class TextSegmentationTaskResult(models.Model):
    STATUS_CHOICES = [
        ("in_progress", "In Progress"),
        ("submitted", "Submitted"),
        ("under_review", "Under Review"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
        ("skipped", "Skipped"),
    ]

    annotator = models.ForeignKey(
        PlanMember, on_delete=models.CASCADE, verbose_name="Annotator", null=True, blank=True
    )
    batch = models.ForeignKey(TextPlan, on_delete=models.CASCADE, null=True)
    batch_data = models.ForeignKey(TextPlanRawData, on_delete=models.CASCADE, null=True)

    # plan_segmentation = models.ForeignKey(
    #     TextSegmentationPlan, on_delete=models.CASCADE, verbose_name="Text Segmentation Plan"
    # )
    plan_segmentation = None
    phase_index = models.CharField(
        max_length=45, verbose_name="Phase Index", help_text="The phase this task belongs to"
    )
    segmentation_result = models.TextField(
        verbose_name="Segmentation Result", help_text="The result of the annotation"
    )
    status = models.CharField(
        max_length=45, choices=STATUS_CHOICES, default="in_progress", verbose_name="Status"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def update_status(self, next_status):
        if self.status != next_status:
            last_status = self.segmentation_history.filter(ended_at__isnull=True).last()
            if last_status:
                last_status.ended_at = now()
                last_status.save()
            TaskSegmentationStatusHistory.objects.create(
                task_segmentation=self,
                status=next_status,
                started_at=now(),
            )
            self.status = next_status
            self.save()

    def __str__(self):
        return f"Task {self.plan_segmentation_id} - {self.segmentation_result} ({self.status})"

    # assign the tasks to annotators who's required to be qualified for these tasks
    def can_access_task(self):
        """Gate access based on qualification."""
        config = self.plan_segmentation.plan_segmentation_conf_id
        if config.is_qualified and config.qualification_test:
            try:
                result = WorkerQualification.objects.get(
                    annotator=self.annotator.profile,
                    qualification_test=config.qualification_test
                )
                return result.passed
            except WorkerQualification.DoesNotExist:
                return False
        return True


class TaskSegmentationStatusHistory(models.Model):
    task_segmentation = models.ForeignKey(TextSegmentationTaskResult, on_delete=models.CASCADE,
                                          related_name="segmentation_history")
    status = models.CharField(max_length=20, choices=TextSegmentationTaskResult.STATUS_CHOICES)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f" {self.task_segmentation} - {self.status} ({self.started_at} - {self.ended_at})"
