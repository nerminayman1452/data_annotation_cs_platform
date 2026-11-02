import os

from django.db import models

from apps.project_management.models.time_stamp import TimeStampedModel
from django.utils.translation import gettext_lazy as _


class BasePlanRawData(TimeStampedModel):
    """
    Abstract Base for Level 2: The Source File.
    Standardizes how files are uploaded and named across the platform.
    """
    file = models.FileField(
        upload_to="batch_source_files/%Y/%m/%d/",
        verbose_name=_("Source File"),
        help_text=_("The original file uploaded (CSV, ZIP, JSON, etc.)")
    )
    file_name = models.CharField(
        max_length=255,
        verbose_name=_("File Name"),
        help_text=_("Original name of the file for display purposes")
    )

    quality = models.CharField(max_length=10, choices=(
        ('good', 'good'), ('bad', 'bad')), default='good')


    class Meta:
        abstract = True

    def __str__(self):
        return self.file_name


    # @property
    # def file_size(self):
    #     if self.file and hasattr(self.file, 'size'):
    #         return self.file.size
    #     return 0
    #
    #
    # @property
    # def file_type(self):
    #     if self.file and hasattr(self.file, 'name'):
    #         return os.path.splitext(self.file.name)[1].lower()
    #     return ''


