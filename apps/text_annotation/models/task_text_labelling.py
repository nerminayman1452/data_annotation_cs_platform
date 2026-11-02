from django.db import models
from django.utils.timezone import now

from apps.project_management.models.plan_members import PlanMember
from apps.project_management.models.text_plan import TextErrorType, TextLabelType, TextSentenceType
from apps.project_management.models.text_plan import TextPlanRawData
# from apps.text_annotation.models.plan_text_labelling import TextLabellingPlan, TextSentenceType, TextLabelType, \
#     TextErrorType
# from apps.project_management.models import BatchMembers, Batch
from apps.text_annotation.models.qualification_config import WorkerQualification


class TextLabellingTaskResult(models.Model):
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
        PlanMember, on_delete=models.CASCADE, verbose_name="Annotator", null =True, blank =True)

    # annotator = models.IntegerField( null=True,blank=True) 
    # )
    # batch = models.ForeignKey(Batch, on_delete=models.CASCADE, null=True)
    batch_data = models.ForeignKey(TextPlanRawData, on_delete=models.CASCADE, null=True) #setnence


    data_content = models.TextField(null=True,blank=True)
    # plan = models.ForeignKey(
    #     TextLabellingPlan, on_delete=models.CASCADE, verbose_name="Text Labelling Plan"
    # )

    # phase_index = models.CharField(
    #     max_length=45, verbose_name="Phase Index", help_text="The phase this task belongs to"
    # ) #in the segmentation task

    # labelling_result = models.CharField(
    #     max_length=255, verbose_name="Labelling Result", help_text="The result of the annotation", null=True,blank=True
    # )

    #todo or enter new label-type
    label_type_result = models.ForeignKey(TextLabelType, on_delete=models.SET_NULL,
                                        verbose_name="Labelling Type Result", help_text="The result of labelling annotation", null=True,blank=True)
    error_type_result = models.ForeignKey(TextErrorType, on_delete=models.SET_NULL,
                                        verbose_name="Error Type Result", help_text="The result of labelling annotation", null=True,blank=True)
    sentence_type_result = models.ForeignKey(TextSentenceType, on_delete=models.SET_NULL,
                                           verbose_name="Sentence Type Result", help_text="The result of labelling annotation", null=True,blank=True)

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
        return f"Task {self.plan_id} - {self.label_type_result} - {self.error_type_result} - {self.sentence_type_result} ({self.status})"

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
    task_labelling = models.ForeignKey(TextLabellingTaskResult, on_delete=models.CASCADE,
                                       related_name="labelling_history")
    status = models.CharField(max_length=20, choices=TextLabellingTaskResult.STATUS_CHOICES)
    #todo the user who began in it
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f" {self.task_labelling} - {self.status} ({self.started_at} - {self.ended_at})"
