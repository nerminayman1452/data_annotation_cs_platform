from django.db import models
from django.utils.timezone import now

from apps.project_management.models.plan_members import PlanMember
from apps.project_management.models.text_plan import TextPlan, TextValidationType
from apps.project_management.models.text_plan import TextPlanRawData
# from apps.text_annotation.models.plan_text_validation import (TextValidationPlan)
# , TextValidationType)
# BatchMembers,
from apps.text_annotation.models.qualification_config import WorkerQualification


class TextValidationTaskResult(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
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
    batch_data = models.ForeignKey(TextPlanRawData, on_delete=models.SET_NULL, null=True)
    data_content = models.TextField(null=True,blank=True)
    # plan = models.ForeignKey(
    #     TextValidationPlan, on_delete=models.CASCADE, verbose_name="Text Validation Plan"
    # )
    plan = None

    # validation_result = models.CharField(
    #     max_length=255, verbose_name="Validation Result", help_text="The result of the annotation"
    # )

    validate_type_result = models.ForeignKey(
        TextValidationType, on_delete=models.SET_NULL, verbose_name="Text Validation Type Result",
        help_text="The result of the validation annotation", null=True,blank=True
    )

    status = models.CharField(
        max_length=45, choices=STATUS_CHOICES, default="in_progress", verbose_name="Status"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def update_status(self, next_status):
        if self.status != next_status:
            last_status = self.validation_history.filter(ended_at__isnull=True).last()
            if last_status:
                last_status.ended_at = now()
                last_status.save()
            TaskValidationStatusHistory.objects.create(
                task_validation=self,
                status=next_status,
                started_at=now(),
            )
            self.status = next_status
            self.save()

    def __str__(self):
        return f"Task {self.plan_id} - {self.validate_type_result} ({self.status})"

    # assign the tasks to annotators who's required to be qualified for these tasks
    def can_access_task(self):
        """Gate access based on qualification."""
        config = self.plan.plan_validation_conf_id
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


class TaskValidationStatusHistory(models.Model):
    task_validation = models.ForeignKey(TextValidationTaskResult, on_delete=models.CASCADE,
                                        related_name="validation_history")
    status = models.CharField(max_length=20, choices=TextValidationTaskResult.STATUS_CHOICES)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f" {self.task_validation} - {self.status} ({self.started_at} - {self.ended_at})"



