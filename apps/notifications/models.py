from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class Notification(models.Model):
    # Notification types for different actions
    NOTIFICATION_TYPES = [
        # Project related
        ('project_created', _('Project Created')),
        ('project_updated', _('Project Updated')),
        ('project_completed', _('Project Completed')),
        
        # Batch related
        ('batch_created', _('Batch Created')),
        ('batch_assigned', _('Batch Assigned')),
        ('batch_completed', _('Batch Completed')),
        
        # Task related
        ('task_assigned', _('Task Assigned')),
        ('task_submitted', _('Task Submitted')),
        ('task_accepted', _('Task Accepted')),
        ('task_rejected', _('Task Rejected')),
        ('task_completed', _('Task Completed')),
        
        # Invitation related
        ('invitation_sent', _('Invitation Sent')),
        ('invitation_accepted', _('Invitation Accepted')),
        ('invitation_declined', _('Invitation Declined')),
        ('invitation_expired', _('Invitation Expired')),
        
        # Review related
        ('review_requested', _('Review Requested')),
        ('review_completed', _('Review Completed')),
        ('review_feedback', _('Review Feedback')),
        
        # System related
        ('system_alert', _('System Alert')),
        ('announcement', _('Announcement')),
    ]

    # Recipient of the notification
    user = models.ForeignKey(
        get_user_model(), 
        on_delete=models.CASCADE, 
        related_name='notifications',
        verbose_name=_('recipient')
    )
    
    # Sender of the notification (can be null for system notifications)
    sender = models.ForeignKey(
        get_user_model(), 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='sent_notifications',
        verbose_name=_('sender')
    )
    
    notification_type = models.CharField(
        _('type'),
        max_length=20, 
        choices=NOTIFICATION_TYPES
    )
    title = models.CharField(_('title'), max_length=200)
    message = models.TextField(_('message'))
    is_read = models.BooleanField(_('read'), default=False)
    created_at = models.DateTimeField(_('created at'), default=timezone.now)
    data = models.JSONField(_('data'), default=dict, blank=True)
    modified_at = models.DateTimeField(_('modified at'), auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('notification')
        verbose_name_plural = _('notifications')
        indexes = [
            models.Index(fields=['user', 'is_read', 'created_at']),
            models.Index(fields=['notification_type']),
        ]
        

    def send_email(self):
        """Send email notification"""
        subject = f"Notification: {self.title}"
        
        # Simple text email
        email_message = f"""
        {self.message}
        
        This is an automated message. Please do not reply to this email.
        """
        
        if self.notification_type == 'invitation_sent':
            email_message += f"\n\nTo accept this invitation, click here: {self.data.get('accept_url', '#')}"
            email_message += f"\nTo decline: {self.data.get('decline_url', '#')}"

        try:
            send_mail(
                subject=subject,
                message=email_message.strip(),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[self.user.email],
                fail_silently=False,
            )
            return True
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False

    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=['is_read', 'modified_at'])

class NotificationService:
    @classmethod
    def create_notification(cls, user, notification_type, title, message, data=None, send_email=True):
        """Create and send a notification"""
        notification = Notification.objects.create(
            user=user,
            notification_type=notification_type,
            title=title,
            message=message,
            data=data or {}
        )
        
        if send_email:
            notification.send_email()
            
        return notification
