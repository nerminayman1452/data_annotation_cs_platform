from django.contrib import admin

from apps.image_annotation.models.plan_task import ImagePlanTask
from apps.image_annotation.models.task_annotation import ImageTaskAnnotation

admin.site.register(ImagePlanTask)
admin.site.register(ImageTaskAnnotation)
