from django.db import models

from apps.tasks.models.plan_task import BasePlanTask
from apps.project_management.models import PlanMember


class ImagePlanTask(BasePlanTask):
    """
    Specific implementation for Image.
    """
    plan = models.ForeignKey(
        'project_management.ImagePlan',
        on_delete=models.CASCADE,
        related_name="plan_tasks"
    )

    plan_file = models.ForeignKey(
        'project_management.ImagePlanRawData',
        on_delete=models.CASCADE,
        related_name="raw_data_tasks"
    )

    # UPDATED: Through model is now the merged Annotation model
    members = models.ManyToManyField(
        PlanMember,
        through='ImageTaskAnnotation',
        related_name='assigned_image_tasks',
    )

    def __str__(self):
        return f"Item {self.id} in {self.plan}"


#todo - annotations and annotators progress on the tasks 
# class ImageClassificationAnnotationQuerySet(models.QuerySet):
#     """
#     custom queryset for returning annotator progress
#     """
#     def progress_for_annotator(self, member, plan_id):
#         total_assigned = self.filter(annotator=member, task__plan_id=plan_id).count()
#         completed = self.filter(
#             annotator=member, task__plan_id=plan_id, status__in=["submitted","accepted","rejected","under_review"]
#         ).count()
#         return {
#             "annotator_id": member.id,
#             "total_assigned": total_assigned,
#             "total_completed": completed,
#             "remaining": max(total_assigned - completed, 0),
#             "progress_percent": round((completed / total_assigned * 100) if total_assigned else 0, 2),
#         }

# class ImageClassificationAnnotationManager(models.Manager):
#     #ImageClassificationAnnotation.objects.progress_for_annotator(...)
#     def get_queryset(self):
#         return BaseAnnotationQuerySet(self.model, using=self._db)

#     # convenience passthrough
#     def progress_for_annotator(self, member, plan_id):
#         return self.get_queryset().progress_for_annotator(member, plan_id)


# class ImageClassificationAnnotation(BaseImageAnnotation):
#     task = models.ForeignKey(ImageClassificationTask, on_delete=models.CASCADE, related_name="annotations")

#     label_type_result = models.ForeignKey(
#         ImageLabelType,
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True
#     )

#     objects = ImageClassificationAnnotationManager()

#     class Meta(BaseImageAnnotation.Meta):
#         unique_together = ("task", "annotator")

#     def clean(self):
#         self.clean_label(self.label_type_result)
    
#     def save(self, *args, **kwargs):
#         self.full_clean()
#         super().save(*args, **kwargs)

#     def __str__(self):
#         label_display = self.label_type_result or self.custom_label or "No Label"
#         return f"Annotation #{self.id} by {self.annotator} - {label_display} - {self.status}"


#todo - tasks history
# class ImageClassificationStatusHistory(BaseAnnotationStatusHistory):
#     annotation = models.ForeignKey(ImageClassificationAnnotation, on_delete=models.CASCADE, related_name="status_history")

