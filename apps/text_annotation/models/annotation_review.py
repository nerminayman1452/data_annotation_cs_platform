# from django.db import models
#
# from apps.tasks.models.annotation_review import BaseAnnotationReview
# from apps.text_annotation.models.annotation_task_assignment import TextAnnotationSubmission
#
#
# class TextAnnotationReview(BaseAnnotationReview):
#     """
#     Review specifically for a Text Submission.
#     """
#     annotation_submission = models.OneToOneField(
#         TextAnnotationSubmission,
#         on_delete=models.CASCADE,
#         related_name="review"
#     )
#
#     def __str__(self):
#         return f"Text Review for Sub {self.annotation_submission.id}"
