from django.db import models


class TimeStampedModel(models.Model):
    """
    Abstract base class to ensure all models have consistent timestamping.
    """
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        abstract = True
