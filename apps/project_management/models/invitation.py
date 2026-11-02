from django.db import models
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

class PlanInvitation(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('expired', 'Expired')
    ]
    
    # Generic foreign key to any plan type (ImagePlan, TextPlan, etc.)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveBigIntegerField()
    plan = GenericForeignKey('content_type', 'object_id')
    
    email = models.EmailField()
    role = models.CharField(
        max_length=20,
        choices=[
            ("Annotator", "Annotator"),
            ("Reviewer", "Reviewer"),
        ],
    )
    token = models.CharField(max_length=64, unique=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    invited_by = models.IntegerField()  # User ID of the inviter
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        unique_together = ('content_type', 'object_id', 'email', 'status')
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
        ]
        
    def is_expired(self):
        return timezone.now() > self.expires_at
        
    def __str__(self):
        return f"{self.email} - {self.object_id} - {self.role}"