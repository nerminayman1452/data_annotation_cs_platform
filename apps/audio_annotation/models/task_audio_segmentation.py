from django.db import models
from django.utils.timezone import now

from apps.audio_annotation.models.plan_audio_segmentation import AudioSegmentationPlan
from apps.project_management.models.audio_plan import AudioPlan
from apps.project_management.models.audio_plan import AudioPlanRawData


class AudioSegmentationTaskResult(models.Model):
    STATUS_CHOICES = [
        ("in_progress", "In Progress"),
        ("submitted", "Submitted"),
        ("under_review", "Under Review"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
        ("skipped", "Skipped"),
    ]

    # annotator = models.ForeignKey(
    #     BatchMembers, on_delete=models.CASCADE, verbose_name="Annotator"
    # )
    batch = models.ForeignKey(AudioPlan, on_delete=models.CASCADE, null=True)
    batch_data = models.ForeignKey(AudioPlanRawData, on_delete=models.CASCADE, null=True)

    plan_segmentation = models.ForeignKey(
        AudioSegmentationPlan, on_delete=models.CASCADE, verbose_name="Audio Segmentation Plan"
    )
    phase_index = models.CharField(
        max_length=45, verbose_name="Phase Index", help_text="The phase this task belongs to"
    )
    segmentation_result = models.TextField(
        verbose_name="Segmentation Result", help_text="The result of the annotation"
    )
    status = models.CharField(
        max_length=45, choices=STATUS_CHOICES, default="in_progress", verbose_name="Status"
    )
    segment_start_time = models.FloatField()  # in seconds
    segment_end_time = models.FloatField()  # in seconds

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


class TaskSegmentationStatusHistory(models.Model):
    task_segmentation = models.ForeignKey(AudioSegmentationTaskResult, on_delete=models.CASCADE,
                                          related_name="segmentation_history")
    status = models.CharField(max_length=20, choices=AudioSegmentationTaskResult.STATUS_CHOICES)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f" {self.task_segmentation} - {self.status} ({self.started_at} - {self.ended_at})"
