from django.db import models
from django.utils.timezone import now

from apps.audio_annotation.models.plan_audio_labelling import AudioLabellingPlan
from apps.project_management.models.plan_members import PlanMember
from apps.project_management.models.audio_plan import AudioPlan
from apps.project_management.models.audio_plan import AudioPlanRawData
from apps.text_annotation.models.qualification_config import WorkerQualification


class AudioLabellingTaskResult(models.Model):
    STATUS_CHOICES = [
        ("in_progress", "In Progress"),
        ("submitted", "Submitted"),
        ("under_review", "Under Review"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
        ("skipped", "Skipped"),

    ]
    annotator = models.ForeignKey(
        PlanMember, on_delete=models.CASCADE, verbose_name="Annotator", null=True
    )

    template_task = models.ForeignKey('self', on_delete=models.CASCADE,
                                      null=True,
                                      blank=True,
                                      related_name='child_results',
                                      help_text="Points to the original template result")
    batch = models.ForeignKey(AudioPlan, on_delete=models.CASCADE, null=True)
    batch_data = models.ForeignKey(AudioPlanRawData, on_delete=models.CASCADE, null=True)
    plan = models.ForeignKey(AudioLabellingPlan, on_delete=models.CASCADE, related_name="task_results")
    task_name = models.CharField(max_length=255)
    submitted_at = models.DateTimeField(auto_now_add=True)
    result = models.JSONField(default=list)
    comments = models.TextField(blank=True, null=True)
    def __str__(self):
        return f"{self.task_name} by {self.annotator}"
    status = models.CharField(
        max_length=45, choices=STATUS_CHOICES, default="in_progress", verbose_name="Status"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def update_status(self, next_status):
        if self.status != next_status:
            last_status = self.labelling_history.filter(ended_at__isnull=True).last()
            if last_status:
                last_status.ended_at = now()
                last_status.save()
            TaskLabellingStatusHistory.objects.create(
                task_labelling=self,
                status=next_status,
                started_at=now(),
            )
            self.status = next_status
            self.save()

    def __str__(self):
        return f"Task {self.plan} ({self.status})"

    # assign the tasks to annotators who's required to be qualified for these tasks
    def can_access_task(self):
        """Gate access based on qualification."""
        config = self.plan.plan_labelling_conf_id
        if config.is_qualified and config.qualification_test:
            try:
                result = WorkerQualification.objects.get(
                    annotator=self.annotator.profile,
                    qualification_test=config.qualification_test
                )
                return result.passed
            except WorkerQualification.DoesNotExist:
                return False
        # If no qualification is required, then can be assigned to the task
        return True


class TaskLabellingStatusHistory(models.Model):
    task_labelling = models.ForeignKey(AudioLabellingTaskResult, on_delete=models.CASCADE,
                                       related_name="labelling_history")
    status = models.CharField(max_length=20, choices=AudioLabellingTaskResult.STATUS_CHOICES)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f" {self.task_labelling} - {self.status} ({self.started_at} - {self.ended_at})"
