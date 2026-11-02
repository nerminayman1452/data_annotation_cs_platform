from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Notification

@receiver(post_save, sender=Notification)
def send_notification_email(sender, instance, created, **kwargs):
    """Send email notification when a new notification is created"""
    if created and instance.notification_type != 'invitation_sent':
        instance.send_email()
