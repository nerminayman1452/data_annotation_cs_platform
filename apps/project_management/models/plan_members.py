from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from apps.profile.models.profile import Role

class PlanMember(models.Model):
    # profile = models.ForeignKey("Profile", on_delete=models.CASCADE)
    profile = models.IntegerField(null=True, blank=True)
    role = models.CharField(max_length=20, choices=Role.choices,default=Role.ANNOTATOR)
    # 2. The "Table Selector" (Points to Django's internal list of models)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    # 3. The "Row Selector" (Stores the ID of the specific plan)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    # 4. The Magic Link (This doesn't exist in the DB, it's a Python helper)
    plan = GenericForeignKey('content_type', 'object_id')

    class Meta:
        # Prevent adding the same user to the same plan twice
        unique_together = ('profile', 'content_type', 'object_id')
        
    def __str__(self):
        return f"{self.profile} working on {self.plan}"


