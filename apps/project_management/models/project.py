from decimal import Decimal
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from apps.helpers.safe_dev import safe_div
from apps.project_management.models.organization import Organization
from apps.project_management.models.time_stamp import TimeStampedModel


class ProjectEstimates:
    """
    Aggregates Budget, Time, and Quantity Targets from all Batches.
    """
    def __init__(self, project):
        self.project = project
        # Use prefetched batches if available, otherwise fetch them
        self._batches = getattr(project, '_prefetched_batches', 
                            getattr(project, '_prefetched_objects_cache', {}).get('batches', project.batches.all()))

    @property
    def total_cost(self):
        return sum(
            (b.estimates.total_cost or 0)
            for b in self._batches 
            if hasattr(b, 'estimates') and b.estimates is not None
        )

    @property
    def total_units(self):
        """Total projected units (manual counts) across all batches."""
        return sum(
            b.estimates.total_units 
            for b in self._batches 
            if hasattr(b, 'estimates') and b.estimates is not None
        )

    @property
    def total_efforts(self):
        """Total Man-Days required across all batches."""
        # Use pre-calculated value if available
        if hasattr(self.project, '_total_efforts'):
            return self.project._total_efforts
            
        # Fallback to calculating from batches if not pre-calculated
        return sum(
            b.estimates.total_efforts 
            for b in self._batches 
            if hasattr(b, 'estimates') and b.estimates is not None
        )

    @property
    def daily_efforts(self):
        """Average daily efforts required based on total efforts and project duration."""
        duration_days = self.duration_days
        return round(safe_div(self.total_efforts, duration_days), 2) if duration_days > 0 else 0

    @property
    def tasks_per_day(self):
        """Average number of tasks to be completed per day to meet the deadline."""
        total_units = self.total_units
        duration_days = self.duration_days
        return round(safe_div(total_units, duration_days), 2) if duration_days > 0 else 0

    @property
    def total_plans_count(self):
        """Total number of plan objects created."""
        # Check if the project has the annotated field
        if hasattr(self.project, 'actual_plans_count'):
            return self.project.actual_plans_count
            
        # Fallback to counting plans manually
        count = 0
        for batch in self._batches:
            # Use prefetched plans if available
            if hasattr(batch, '_prefetched_objects_cache'):
                count += len(batch._prefetched_objects_cache.get('imageplan', []))
                count += len(batch._prefetched_objects_cache.get('textplan', []))
            else:
                count += len(batch.get_all_plans())
        return count

    @property
    def start_date(self):
        """Earliest start date among all batches."""
        dates = [b.estimates.start_date for b in self._batches if b.estimates.start_date]
        return min(dates) if dates else None

    @property
    def end_date(self):
        """Latest estimated end date among all batches."""
        dates = [b.estimates.end_date for b in self._batches if b.estimates.end_date]
        return max(dates) if dates else None
        
    @property
    def duration_days(self):
        """Total project duration in days."""
        start = self.start_date
        end = self.end_date
        if start and end:
            return (end - start).days + 1  # Include both start and end days
        return 0

    @property
    def duration_weeks(self):
        """Total project duration in weeks."""
        days = self.duration_days
        return round(days / 5, 2) if days > 0 else 0


class ProjectActuals:
    """
    Aggregates Real Spend, Progress, and Quality from all Batches.
    """
    def __init__(self, project):
        self.project = project
        # Use prefetched batches if available, otherwise fetch them
        self._batches = getattr(project, '_prefetched_batches', 
                            getattr(project, '_prefetched_objects_cache', {}).get('batches', project.batches.all()))
    @property
    def total_cost(self):
        # FIX 2: Handle None
        return sum(
            (b.actuals.total_cost or 0)
            for b in self._batches 
            if hasattr(b, 'actuals') and b.actuals is not None
        )

    @property
    def total_units(self):
        """Total actual raw data units loaded across all batches."""
        return sum(
            b.actuals.total_units 
            for b in self._batches 
            if hasattr(b, 'actuals') and b.actuals is not None
        )

    @property
    def progress(self):
        if not self._batches:
            return 0.0
        
        # FIX 2: Handle None
        total_progress = sum(
            Decimal(b.actuals.progress_percent or 0) if hasattr(b, 'actuals') and b.actuals else 0
            for b in self._batches
        )
        return round(float(total_progress) / len(self._batches), 2)

    @property
    def weight_times_progress(self):
        """Calculate weight * progress for the project."""
        return sum(
            (getattr(b, 'weight', 0) * getattr(b.actuals, 'progress_percent', 0)) 
            for b in self._batches 
            if hasattr(b, 'actuals') and b.actuals is not None
        )

    @property
    def quality(self):
        """
        Overall Project Quality (Approval Rate).
        Weighted by the volume of work reviewed in each batch.
        """
        total_weighted_quality = 0
        total_reviewed = 0
        
        for batch in self._batches:
            # Get batch quality and reviewed count using the batch's own calculation
            batch_quality = getattr(batch.actuals, 'quality', 0)
            
            # Calculate reviewed items for this batch
            batch_reviewed = 0
            if hasattr(batch, '_prefetched_objects_cache'):
                # Get all plans from prefetched data
                plans = []
                if 'imageplan' in batch._prefetched_objects_cache:
                    plans.extend(batch._prefetched_objects_cache['imageplan'])
                if 'textplan' in batch._prefetched_objects_cache:
                    plans.extend(batch._prefetched_objects_cache['textplan'])
                
                batch_reviewed = sum(
                    getattr(p, 'accepted_count', 0) + getattr(p, 'rejected_count', 0)
                    for p in plans
                )
            else:
                # Fallback to get_all_plans() if not prefetched
                batch_reviewed = sum(
                    getattr(p, 'accepted_count', 0) + getattr(p, 'rejected_count', 0)
                    for p in batch.get_all_plans()
                )
            
            # Only include batches with actual reviews in the calculation
            if batch_reviewed > 0:
                total_weighted_quality += batch_quality * batch_reviewed
                total_reviewed += batch_reviewed
        
        # Calculate weighted average quality
        return round(safe_div(total_weighted_quality, total_reviewed), 2) if total_reviewed > 0 else 0

    @property
    def time_elapsed_percent(self):
        """Time elapsed relative to the overall project schedule."""
        start = self.project.estimates.start_date
        end = self.project.estimates.end_date
        current_date = timezone.now().date()

        if not start or not end or current_date <= start:
            return 0.0
        if current_date >= end:
            return 100.0

        total_days = (end - start).days + 1  # Include both start and end days
        elapsed = (current_date - start).days + 1  # Include current day
        return round(safe_div(elapsed, total_days) * 100, 2)

    @property
    def total_members(self):
        #todo the total num of all batches, if need the total num of unique members
        """
        Total number of members assigned to this project.
        Aggregates directly from Batch Actuals since that logic is verified to work.
        """
        # FIX: Delegate to b.actuals.total_members instead of counting manually from plans
        return sum(
            (b.actuals.total_members or 0) 
            for b in self._batches 
            if hasattr(b, 'actuals') and b.actuals is not None
        )

    @property
    def total_plans_count(self):
        """Total number of plans in this project."""
        # Check if the project has the annotated field
        if hasattr(self.project, 'actual_plans_count'):
            return self.project.actual_plans_count
            
        # Fallback to counting plans manually
        count = 0
        for batch in self._batches:
            # Use prefetched plans if available
            if hasattr(batch, '_prefetched_objects_cache'):
                count += len(batch._prefetched_objects_cache.get('imageplan', []))
                count += len(batch._prefetched_objects_cache.get('textplan', []))
            else:
                count += len(batch.get_all_plans())
        return count

    @property
    def total_plans_types(self):
        """Get all unique plan types in this project."""
        plan_types = set()
        for batch in self._batches:
            if hasattr(batch, '_prefetched_objects_cache'):
                if 'imageplan' in batch._prefetched_objects_cache and batch._prefetched_objects_cache['imageplan']:
                    plan_types.add('image')
                if 'textplan' in batch._prefetched_objects_cache and batch._prefetched_objects_cache['textplan']:
                    plan_types.add('text')
            else:
                plan_types.update(batch.total_plans_types)
        return list(plan_types)

class Project(TimeStampedModel):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="projects",
        null=True
    )
    created_by = models.IntegerField(null=True, blank=True)

    project_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Project Name"),
        help_text=_("Public display name of the project"),
    )

    project_description = models.CharField(
        max_length=255, null=True, verbose_name=_("Project Description")
    )

    is_archived = models.BooleanField(default=False)

    # --- Namespace Hooks ---
    @property
    def estimates(self):
        return ProjectEstimates(self)

    @property
    def actuals(self):
        return ProjectActuals(self)

    @property
    def get_batches(self):
        """Return batches for this project.

        Uses a prefetched batches list when available, otherwise falls back
        to the related manager's queryset (`self.batches.all()`).
        """
        return getattr(self, '_prefetched_batches',
                       getattr(self, '_prefetched_objects_cache', {}).get('batches', self.batches.all()))

    @property
    def weight(self):
        """Calculate total weight of the project based on its batches."""
        batches = self.get_batches
        return sum(getattr(batch, 'weight', 0) for batch in batches)

    def __str__(self):
        return self.project_name