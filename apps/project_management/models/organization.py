from django.db import models

from apps.project_management.models.time_stamp import TimeStampedModel


# --- Core Organization Models ---

class Organization(TimeStampedModel):
    # created_by = models.ForeignKey(
    #     "Profile",
    #     on_delete=models.PROTECT,
    #     related_name="organizations_created"
    # )
    created_by = models.IntegerField(null=True, blank=True)
    name = models.CharField(max_length=255, null=False, blank=False)
    contact_email = models.EmailField(unique=True, null=False, blank=False)
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if self.contact_email:
            self.contact_email = self.contact_email.strip().lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name}"
