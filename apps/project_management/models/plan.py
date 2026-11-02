from decimal import Decimal
import random

from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.helpers.safe_dev import safe_div
from apps.project_management.models.batch import Batch
from apps.project_management.models.plan_members import PlanMember
from apps.project_management.models.time_stamp import TimeStampedModel


class BasePlan(TimeStampedModel):
    """
    Combines the concept of 'Planning' and 'SubProject' from Label Studio.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('paused', 'Paused'),
        ('archived', 'Archived'),
    ]

    batch = models.ForeignKey(
        Batch, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="%(class)s"
    )
    # original_task = models.OneToOneField('self', on_delete=models.SET_NULL, blank=True, null=True)
    # created_by = models.ForeignKey(
    #     "Profile", on_delete=models.PROTECT, related_name="%(class)s_created"
    # )
    created_by = models.IntegerField(null=True, blank=True)

    # Basic Info
    name = models.CharField(max_length=255, null=True, verbose_name=_("Task Name"))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Timing
    actual_end_date = models.DateTimeField(blank=True, null=True, help_text="When the batch actually finished")
    is_locked = models.BooleanField(default=False)
    is_review_plan = models.BooleanField(default=False)

    # Relationship to BatchMembers
    members = GenericRelation(PlanMember)

    class Meta:
        abstract = True

    # --- Abstract Hooks (Subclasses MUST implement these) ---
    def get_task_model(self):
        """Returns the specific Task Unit model (e.g. TextPlanTask)"""
        raise NotImplementedError

    def get_annotation_model(self):
        """Returns the specific Merged Annotation model (e.g. TextTaskAnnotation)"""
        raise NotImplementedError

    def get_raw_unit_count(self):
        # Todo discuss with salah
        """Returns the count of raw data units"""
        raise NotImplementedError

    def get_history_model(self):
        """Returns the specific History model"""
        raise NotImplementedError

    def get_config(self):
        """Returns the configuration for this batch"""
        raise NotImplementedError

    def get_cost_config(self):
        """Returns the cost configuration for this batch"""
        raise NotImplementedError

    def get_estimation_config(self):
        """Returns the estimation configuration for this batch"""
        raise NotImplementedError

    @classmethod
    def generate_unique_int_id(cls):
        """
        Generates a random 64-bit integer.
        Range: 10^14 to (2^63 - 1)
        This ensures the ID is always positive and large enough to be unique.
        """
        return random.randint(100_000_000, 9_223_372_036_854)


    @property
    def total_workforce(self):
        # Return the count of members directly from the GenericRelation
        return self.members.count()

    @property
    def total_tasks_count(self):
        # todo discuss with salah (which num (the actual or estimated) and he workers who will work on)
        return self.get_raw_unit_count()

    @property
    def total_actual_units(self):
        return self.get_raw_unit_count()

    @property
    def assigned_count(self):
        SubModel = self.get_annotation_model()
        return SubModel.objects.filter(
            plan_task__plan=self,
            status='ASSIGNED'
        ).count()

    @property
    def labelled_count(self):
        SubModel = self.get_annotation_model()
        return SubModel.objects.filter(
            plan_task__plan=self,
            status__in=['SUBMITTED', 'ACCEPTED', 'REJECTED']
        ).count()

    @property
    def under_review_count(self):
        SubModel = self.get_annotation_model()
        return SubModel.objects.filter(
            plan_task__plan=self,
            status='SUBMITTED'
        ).count()

    @property
    def accepted_count(self):
        SubModel = self.get_annotation_model()
        return SubModel.objects.filter(
            plan_task__plan=self, status='ACCEPTED'
        ).count()

    @property
    def rejected_count(self):
        SubModel = self.get_annotation_model()
        return SubModel.objects.filter(
            plan_task__plan=self, status='REJECTED'
        ).count()

    @property
    def actual_progress(self):
        # todo discuss with salah ( estimatated progress ??)
        """Actual completion % against the Target."""
        try:
            # Access the config related to this batch (via OneToOne)
            # We assume the related name is always 'config'
            estimation_config = self.get_estimation_config()
            target = estimation_config.total_assignments
            completed_work = self.labelled_count
            return round(safe_div(completed_work, target) * 100, 2)
            
        except (AttributeError, Exception):
            return 0.0

    @property
    def progress_till_now(self):
        """Progress till now % against the current tasks."""
        try:
            return round(safe_div(self.labelled_count, self.total_tasks_count) * 100, 2)
        except (AttributeError, Exception):
            return 0.0

    @property
    def actual_quality(self):
        total_reviewed = self.accepted_count + self.rejected_count
        return round(safe_div(self.accepted_count, total_reviewed) * 100, 2)

    # --- Strategic Metrics Logic ---

    @property
    def weight(self):
        """Relative size of this plan compared to the total batch."""
        try:
            if not self.batch:
                print("weight batch is None")
                return Decimal("0.00")
            est_config = self.get_estimation_config()
            if not est_config:
                return Decimal("0.00")
                
            efforts = est_config.efforts or Decimal("0.00")
            total_efforts = getattr(self.batch.estimates, 'total_efforts', Decimal("0.00")) or Decimal("0.00")
            
            if not total_efforts or total_efforts <= 0:
                return Decimal("0.00")
                
            weight = safe_div(efforts, total_efforts) * 100
            return round(weight, 2) if weight is not None else Decimal("0.00")
            
        except (AttributeError, ZeroDivisionError, Exception) as e:
            return Decimal("0.00")

    @property
    def weighted_progress(self):
        return round(float(self.weight) * float(safe_div(self.actual_progress, 100)), 2)

    @property
    def rates(self):
        try:
            duration = self.estimation_config.duration_days
            units = self.estimation_config.total_units
            return round(safe_div(units, duration), 2)
        except (AttributeError, Exception):
            return 0.0

    @property
    def total_actual_cost(self):
        """
        Real incurred cost based on ACCEPTED submissions.
        Calculation: Accepted Submissions * Rate
        """
        if not self.cost_config:
            return Decimal("0.00")

        # Calculate Reviewer Cost (if applicable)
        if self.plan.is_review_plan:
            # Assuming reviewers are paid per unit reviewed, regardless of outcome
            # or customize logic here if they are only paid for 'resolutions'
            total_reviews = self.plan.accepted_count + self.plan.rejected_count
            return total_reviews * self.cost_config.cost_per_unit

        # Calculate Worker Cost
        return self.plan.accepted_count * self.cost_config.cost_per_unit

    @property
    def actual_end_date(self):
        """When the status actually changed to Completed."""
        return self.plan.actual_end_date

    @property
    def actual_duration_days(self):
        """Actual duration in days based on actual start and end dates."""
        if self.actual_end_date:
            est_conf = self.get_estimation_config()
            return (self.actual_end_date - est_conf.start_date).days
        return 0

    def update_status(self, next_status):
        if self.status != next_status:
            now = timezone.now()
            HistoryModel = self.get_history_model()

            # Use dynamic related manager or query directly
            # Best practice: Filter the HistoryModel by this batch instance
            last_status = HistoryModel.objects.filter(batch=self, ended_at__isnull=True).last()

            if last_status:
                last_status.ended_at = now
                last_status.save()

            HistoryModel.objects.create(
                batch=self, status=next_status, started_at=now
            )
            self.status = next_status
            if next_status == 'completed':
                self.actual_end_date = now
            self.save()


class BasePlanStatusHistory(TimeStampedModel):
    status = models.CharField(max_length=20, choices=BasePlan.STATUS_CHOICES)
    started_at = models.DateTimeField()
    ended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.plan.name} ({self.status})"
