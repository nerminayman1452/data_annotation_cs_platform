
from django.apps import AppConfig

class ImageAnnotationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.image_annotation'

    def ready(self):
        # import apps.IAA.signals.iaa_checker
        pass