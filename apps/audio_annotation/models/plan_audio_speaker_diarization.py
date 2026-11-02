from django.db import models

from apps.project_management.models.image_plan import ImagePlan
from apps.text_annotation.models.qualification_config import QualificationTest


# from apps.project_management.models.batch import Batchfrom apps.text_annotation.models.qualification_config import QualificationTest


class SpeakerLabel(models.Model):
    speaker_label = models.CharField(max_length=255, verbose_name="Speaker label")

    def __str__(self):
        return self.speaker_label

class PlanSpeakerDiarizationConfig(models.Model):
        annotators_per_task = models.IntegerField(verbose_name="Number of Assigned Annotators")
        maximum_tasks_per_annotator = models.FloatField(verbose_name="Percentage of Maximum Tasks per Annotator")
        reviewers_per_task = models.IntegerField(verbose_name="Number of Assigned Reviewers")
        description = models.TextField(blank=True, null=True, verbose_name="Plan Description")

        # Number of task results to be matched for the same task that needs to be accepted automatically
        acceptance_agreement = models.IntegerField(null=True, blank=True)
        reward_per_task = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Reward per Task",
                                              null=True)

        time_allotted_per_annotator = models.IntegerField(default=30, verbose_name="Time Allotted per Annotator",
                                                          help_text="maximum time in mins an annotator has to complete the labelling")
        duration = models.IntegerField(default=3, help_text="Duration in days", verbose_name="Duration in days")
        auto_approve_time = models.IntegerField(default=1, verbose_name="Auto Approve Time",
                                                help_text="The amount of time you have to reject the annotator's assignment after submitted")
        confidence_score = models.FloatField(verbose_name="Confidence Score Threshold", null=True)

        is_qualified = models.BooleanField(default=False, verbose_name="Qualified",
                                           help_text="Require the annotators be Masters to do tasks")
        min_annotator_approval_rating = models.DecimalField(max_digits=5, decimal_places=2, null=True,
                                                            help_text="the required percentage of worker’s past performance")
        min_approved_tasks = models.IntegerField(default=0, null=True, verbose_name="Total Approved Tasks",
                                                 help_text="the total number of worker's tasks that have been approved")
        # required_locations = models.ManyToManyField(Locations, verbose_name="Required Locations",)
        qualification_test = models.ForeignKey(QualificationTest, on_delete=models.SET_NULL,
                                               null=True, blank=True,
                                               help_text="Optional: Qualification test for annotators")

        question = models.TextField(verbose_name="Annotation Question", null=True)
        keywords = models.TextField(verbose_name="Keywords", null=True,
                                    help_text="keywords help workers (annotators) search for the task")

        def __str__(self):
            return self.description

class AudioSpeakerDiarizationPlan(models.Model):
    plan_name = models.CharField(max_length=255)
    plan_speaker_diarization_conf_id = models.OneToOneField(PlanSpeakerDiarizationConfig, on_delete=models.SET_NULL, null=True)
    batch = models.ForeignKey(ImagePlan, on_delete=models.CASCADE, null=True)
    speaker_labels = models.ManyToManyField(SpeakerLabel)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.plan_name
