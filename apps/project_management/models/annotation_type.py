from django.db import models
from django.utils.translation import gettext_lazy as _


class AnnotationType(models.Model):
    class PlanType(models.TextChoices):
        TEXT = 'TEXT', _('Text')
        IMAGE = 'IMAGE', _('Image')
        AUDIO = 'AUDIO', _('Audio')
        # VIDEO = 'VIDEO', _('Video')  # Ready for future expansion

    name = models.CharField(max_length=128, help_text="e.g. 'Bounding Box', 'Summarization'")
    url = models.CharField(max_length=128, help_text="e.g. 'http://example.com'", null=True, blank=True)
    plan_type = models.CharField(
        max_length=10,
        choices=PlanType.choices,
        db_index=True
    )
    comparison_key = models.JSONField(
        default=list,
        help_text="The JSON key to use for consensus (e.g. ['label', 'sentiment', 'boxes'])"
    )

    class Meta:
        verbose_name = "Annotation Type"
        verbose_name_plural = "Annotation Types"
        unique_together = ['name', 'plan_type']

    def __str__(self):
        return f"{self.plan_type} - {self.name}"





