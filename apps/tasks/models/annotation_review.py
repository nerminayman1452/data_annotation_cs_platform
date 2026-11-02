# from django.db import models
#
# from apps.project_management.models.plan_members import PlanMember
# from apps.project_management.models.time_stamp import TimeStampedModel
#
#
# class BaseAnnotationReview(TimeStampedModel):
#     """
#     Abstract base for reviews (Feedback loop).
#     Stores who reviewed it, when, and the text feedback.
#     """
#     reviewer = models.ForeignKey(
#         PlanMember,
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#         related_name="%(class)s_reviews"
#     )
#
#     feedback = models.TextField(blank=True, help_text="Reviewer comments")
#
#     # Standardized decision choices
#     # decision_type = models.CharField(
#     #     max_length=20,
#     #     choices=[
#     #         ('ACCEPTED', 'Accepted'),
#     #         ('REJECTED', 'Rejected'),
#     #         ('CORRECTED', 'Corrected'),  # If reviewer fixes it themselves
#     #     ],
#     #     default='ACCEPTED'
#     # )
#
#     class Meta:
#         abstract = True