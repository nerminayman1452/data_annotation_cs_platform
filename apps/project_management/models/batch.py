from itertools import chain
from decimal import Decimal
import math
from django.db import models
from django.utils.timezone import now
from django.utils import timezone

from apps.helpers.safe_dev import safe_div
from apps.project_management.models.project import Project
from apps.project_management.models.time_stamp import TimeStampedModel

class BatchEstimates:
    """Aggregates Target/Budgeted values from all child Plans."""
    def __init__(self, batch):
        self.batch = batch
        self._plans = batch.get_all_plans()

    @property
    def total_cost(self):
        total = 0
        for plan in self._plans:
            try:
                cost = plan.cost_config.total_estimated_budget if plan.cost_config else 0
                if cost is not None:
                    total += cost
            except Exception:
                continue
        return total

    @property
    def total_units(self):
        """Sum of manual unit counts (Raw Data Quantity)."""
        return sum(
            p.get_estimation_config().total_units 
            for p in self._plans 
            if hasattr(p, 'get_estimation_config') and p.get_estimation_config() is not None
        )
    
    @property
    def total_assignments(self):
        """Total Assignments (Units * Redundancy)."""
        return sum(
            p.get_estimation_config().total_assignments 
            for p in self._plans 
            if hasattr(p, 'get_estimation_config') and p.get_estimation_config() is not None
        )

    @property
    def total_efforts(self):
        """Total Man-Days required."""
        return sum(
            p.get_estimation_config().efforts 
            for p in self._plans 
            if hasattr(p, 'get_estimation_config') and p.get_estimation_config() is not None
        )

    @property
    def start_date(self):
        dates = [
            p.get_estimation_config().start_date 
            for p in self._plans 
            if hasattr(p, 'get_estimation_config') and 
               p.get_estimation_config() is not None and 
               getattr(p.get_estimation_config(), 'start_date', None) is not None
        ]
        return min(dates) if dates else None

    @property
    def end_date(self):
        dates = [
            p.get_estimation_config().estimated_end_date 
            for p in self._plans 
            if hasattr(p, 'get_estimation_config') and 
               p.get_estimation_config() is not None and 
               getattr(p.get_estimation_config(), 'estimated_end_date', None) is not None
        ]
        return max(dates) if dates else None

    @property
    def duration_days(self):
        start = self.start_date
        end = self.end_date
        if start and end:
            return (end - start).days
        return 0
    
    @property
    def duration_weeks(self):
        return math.ceil(safe_div(self.duration_days, 5))

    # @property
    # def total_workers(self):
    #     """Total number of workers assigned to this batch."""
    #     return sum(p.get_estimation_config().total_workers for p in self._plans)

    # --- Throughput Metrics ---
    
    @property
    def daily_unit_throughput(self):
        """Target Units (Raw Data) finished Per Day."""
        return math.ceil(safe_div(self.total_units, self.duration_days))

    @property
    def daily_assignment_throughput(self):
        """Target Submissions (Workload) Per Day."""
        return math.ceil(safe_div(self.total_assignments, self.duration_days))

    @property
    def daily_effort(self):
        """Target Man-Days Per Day."""
        return math.ceil(safe_div(self.total_efforts, self.duration_days))


class BatchActuals:
    """Aggregates Real/Execution values from all child Plans."""
    def __init__(self, batch):
        self.batch = batch
        self._plans = batch.get_all_plans()

    @property
    def total_cost(self):
        total = 0
        for plan in self._plans:
            try:
                cost = getattr(plan, 'total_actual_cost', 0)
                if cost is not None:
                    total += cost
            except Exception:
                continue
        return total

    @property
    def total_units(self):
        """Actual raw data loaded."""
        total = 0
        for plan in self._plans:
            try:
                if hasattr(plan, 'get_raw_unit_count'):
                    count = plan.get_raw_unit_count()
                    if count is not None:
                        total += count
            except Exception:
                continue
        return total

    @property
    def progress_percent(self):
        """
        Weighted Average Progress based on Effort.
        Formula: Sum(PlanProgress * PlanEffort) / TotalBatchEffort

        estimated progess based on target assignments (not progress till now in plan)
        """
        try:
            total_effort = self.batch.estimates.total_efforts
            if not total_effort:
                return 0.0
            
            weighted_sum = 0
            for plan in self._plans:
                try:
                    if hasattr(plan, 'get_estimation_config') and hasattr(plan, 'actual_progress'):
                        config = plan.get_estimation_config()
                        if config is not None and hasattr(config, 'efforts'):
                            progress = getattr(plan, 'actual_progress', 0)
                            weighted_sum += Decimal(progress) * Decimal(config.efforts)
                except Exception:
                    continue
            return round(safe_div(weighted_sum, total_effort), 2)
        except Exception:
            return 0.0

    @property
    def time_elapsed_percent(self):
        # try:
        if not hasattr(self.batch, 'estimates'):
            return 0.0
            
        start = getattr(self.batch.estimates, 'start_date', None)
        end = getattr(self.batch.estimates, 'end_date', None)
        current_date = timezone.now().date()

        if not start or not end or current_date <= start:
            return 0.0
        if current_date >= end:
            return 100.0

        total_days = (end - start).days
        elapsed = (current_date - start).days
        return round(safe_div(elapsed, total_days) * 100, 2)

    @property
    def quality(self):
        total_accepted = sum(p.accepted_count for p in self._plans)
        total_reviewed = total_accepted + sum(p.rejected_count for p in self._plans)
        return round(safe_div(total_accepted, total_reviewed) * 100, 2)


    @property
    def weight_times_progress(self):
        """Contribution to Project Completion."""
        return round(Decimal(str(self.batch.weight)) * Decimal(safe_div(self.progress_percent, 100)), 2)

    @property
    def total_members(self):
        """Total number of members assigned to this batch."""
        return sum(p.total_workforce for p in self._plans)

    @property
    def total_plans_count(self):
        """Total number of plans in this batch."""
        return len(self._plans)

    @property
    def total_plans_types(self):
        """Get all unique plan types in this batch."""
        plan_types = set()
        if hasattr(self.batch, '_prefetched_objects_cache'):
            if 'imageplan' in self.batch._prefetched_objects_cache and self.batch._prefetched_objects_cache['imageplan']:
                plan_types.add('image')
            if 'textplan' in self.batch._prefetched_objects_cache and self.batch._prefetched_objects_cache['textplan']:
                plan_types.add('text')
        else:
            plan_types.update(p.plan_type for p in self._plans)
        return list(plan_types)

class Batch(TimeStampedModel):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('archived', 'Archived'),
    ]

    project = models.ForeignKey(
        Project, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="batches"
    )

    name = models.CharField(max_length=256, null=True, blank=True)
    created_by = models.IntegerField(null=True, blank=True)
    total_amount= models.IntegerField(null=True, blank=True)
    # Flags
    is_template = models.BooleanField(null=True, blank=True, default=False)
    is_approved = models.BooleanField(null=True, blank=True, default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # --- Namespace Hooks ---
    @property
    def estimates(self):
        return BatchEstimates(self)

    @property
    def actuals(self):
        return BatchActuals(self)

    # --- Strategic ---
    @property
    def weight(self):
        """Relative size of this batch compared to the whole Project."""
        if not self.project: return Decimal("0.00")
        try:
            # Note: This might be slow if not prefetched. 
            # Ideally Project has a cached total field, but for now we sum dynamically.
            project_total_units = sum(b.estimates.total_units for b in self.project.batches.all())
            return round(safe_div(self.estimates.total_units, project_total_units) * 100, 2)
        except Exception:
            return Decimal("0.00")

    def get_all_plans(self):
        """Aggregates all related plans (Text, Image, etc.)."""
        plan_types = ['textplan', 'imageplan', 'audioplan']
        iterables = []
        for plan_type in plan_types:
            manager = getattr(self, plan_type, None)
            if manager:
                # Optimized for property access
                # Use prefetch_related for reverse OneToOne relations (estimation_config, cost_config)
                iterables.append(manager.all().prefetch_related('config','estimation_config', 'cost_config'))
        return list(chain(*iterables))
    
    def update_status(self, next_status):
        if self.status != next_status:
            last_status = self.batch_history.filter(ended_at__isnull=True).last()
            if last_status:
                last_status.ended_at = now()
                last_status.save()
            BatchStatusHistory.objects.create(batch=self, status=next_status, started_at=now())
            self.status = next_status
            self.save()

    def __str__(self):
        return f"{self.name}"

class BatchStatusHistory(models.Model):
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name="batch_history", null=True)
    status = models.CharField(max_length=20, choices=Batch.STATUS_CHOICES)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)