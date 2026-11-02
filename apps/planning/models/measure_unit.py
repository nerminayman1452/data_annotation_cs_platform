from django.conf import settings
from django.db import models


class MeasureUnits(models.Model):

    title = models.CharField(max_length=100, unique=True)

    created_by = models.BigIntegerField(null = True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
