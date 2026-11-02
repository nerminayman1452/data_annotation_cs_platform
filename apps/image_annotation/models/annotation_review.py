# from django.db import models
#
# from apps.tasks.models.annotation_review import BaseAnnotationReview
# from apps.image_annotation.models.annotation_submission import ImageAnnotationSubmission
#
#
# class ImageAnnotationReview(BaseAnnotationReview):
#     """
#     Review specifically for a Text Submission.
#     """
#     annotation_submission = models.OneToOneField(
#         ImageAnnotationSubmission,
#         on_delete=models.CASCADE,
#         related_name="review"
#     )
#
#     def __str__(self):
#         return f"Text Review for Sub {self.annotation_submission.id}"
