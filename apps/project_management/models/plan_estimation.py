import math
from datetime import timedelta

from django.db import models
from django.utils import timezone

from apps.helpers.safe_dev import safe_div
from apps.project_management.models.time_stamp import TimeStampedModel
from django.utils.translation import gettext_lazy as _


class BaseEstimationConfig(TimeStampedModel):
    """Time & Quantity Engine"""
    start_date = models.DateField(default=timezone.localdate)
    
    #auto_start = models.BooleanField(default=True) --- IGNORE ---
    has_auto_progress = models.BooleanField(default=True)
    total_units = models.DecimalField(
        max_digits=20, decimal_places=2,
        help_text=_('Total quantity (e.g., 100 pages)'), null=True, blank=True, default=0
    )
    duration = models.IntegerField(null=True, blank=True)
    duration_unit = models.CharField(
        max_length=1,
        choices=[('D', 'Days'), ('W', 'Weeks')],
        default='D'
    )
    measure_unit = models.ForeignKey("planning.MeasureUnits", verbose_name=("measure_unit"),
                                     on_delete=models.SET_NULL, null=True, blank=True)
    class Meta:
        abstract = True

    @property
    def total_assignments(self):
        if self.plan.is_review_plan:
            return self.total_units
        return self.total_units * self.plan.config.workers_per_task

    # @property
    # def total_workers(self):
    #     """Total number of workers assigned to this plan."""
    #     return self.plan.config.workers_per_task

    @property
    def efforts(self):
        #man-days
        # Strategy A: Use Standard (Throughput)
        max_tasks = self.plan.config.standard
        if max_tasks and max_tasks > 0:
            return math.ceil(safe_div(self.total_assignments, max_tasks))

        #todo working hours
        # Strategy B: Use Time Per Task
        mins_per_task = self.plan.config.time_per_task
        total_minutes = float(self.total_assignments) * mins_per_task
        total_hours = total_minutes / 60
        return math.ceil(safe_div(total_hours, 8))

    @property
    def efforts_per_worker(self):
        return math.ceil(safe_div(self.efforts, self.plan.config.workers_per_task))

    @property
    def duration_days(self):
        if self.duration and self.duration_unit == 'D':
            return self.duration

        workers = self.plan.config.workers_per_task
        if workers:
            return math.ceil(safe_div(self.efforts, workers))
        return 0

    @property
    def duration_weeks(self):
        if self.duration and self.duration_unit == 'W':
            return self.duration
        return math.ceil(safe_div(self.duration_days, 7))

    @property
    def estimated_end_date(self):
        days = self.duration_days or 0
        return self.start_date + timedelta(days=int(days))
