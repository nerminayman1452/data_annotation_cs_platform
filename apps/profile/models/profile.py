from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.project_management.models.time_stamp import TimeStampedModel


class Role(models.TextChoices):
    MANAGER = "manager", "Manager"
    REVIEWER = "reviewer", "Reviewer"
    ANNOTATOR = "annotator", "Annotator"

class Profile(TimeStampedModel):

    user_id = models.BigIntegerField()
    profile_auth_id = models.IntegerField()
    first_name = models.CharField(_("first name"), max_length=256, blank=True)
    last_name = models.CharField(_("last name"), max_length=256, blank=True)
    email = models.CharField(max_length=256, blank=True)
    role = models.CharField(choices=Role.choices,default=Role.ANNOTATOR, max_length=32)
    last_login = models.DateTimeField(null=True, blank=True)
    weight = models.FloatField(default=1.0)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
