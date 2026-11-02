from django.db import models


class Locations(models.Model):
    """
    available locations required for published tasks
    """
    location = models.CharField(max_length=255, verbose_name="Location")