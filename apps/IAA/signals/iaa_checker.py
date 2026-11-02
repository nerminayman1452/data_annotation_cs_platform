from django.db.models.signals import post_save
from django.dispatch import receiver
# from apps.image_annotation.models.task_img_classification import ImageClassificationAnnotation
# from apps.image_annotation.models.base_models.base_task import AnnotationStatus
# from apps.services.iaa_strategy import IAAStrategy

# @receiver(post_save, sender=ImageClassificationAnnotation)
# def trigger_iaa_check(sender, instance, created, **kwargs):
#     """
#     When an annotation is submitted, check if the task is complete 
#     and run IAA logic.
#     """
#     if instance.status == AnnotationStatus.SUBMITTED:
#         # Check if we should calculate IAA
#         strategy = IAAStrategy(instance.plan)
#         strategy.run()