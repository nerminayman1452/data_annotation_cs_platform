from django.db import models
from apps.project_management.models import Batch

class BatchJoinRequest(models.Model):
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name="join_requests")
    annotator = models.IntegerField(null=True)
    email = models.EmailField(null=True)
    first_name = models.CharField(max_length=100, null=True)
    last_name = models.CharField(max_length=100, null=True)

    status = models.CharField(
        max_length=20,
        choices=[("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected")],
        default="pending"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Meta:
    constraints = [
        models.UniqueConstraint(
            fields=["batch", "annotator"],
            name="unique_batch_annotator"
        )
    ]

    def __str__(self):
        return f"{self.first_name or ''} {self.last_name or ''} → {self.batch} ({self.status})"

