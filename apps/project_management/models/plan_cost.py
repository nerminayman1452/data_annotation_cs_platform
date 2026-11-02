from decimal import Decimal

from django.db import models

from apps.project_management.models.time_stamp import TimeStampedModel
from django.utils.translation import gettext_lazy as _

from config import Config


class BaseCostConfig(TimeStampedModel):
    """Financial Engine"""
    cost_per_unit = models.DecimalField(
        max_digits=10, decimal_places=3, default=0,
        verbose_name=_("Worker Rate")
    )
    # todo in case if the user wanted to create new plan of approved batch
    is_approved = models.BooleanField(default=False)
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    @property
    def calculated_worker_cost(self):
        try:
            total_assignments = self.plan.get_estimation_config().total_assignments
            return Decimal(total_assignments) * self.cost_per_unit
        except Exception:
            return Decimal(0)

    @property
    def total_cost(self):
        return self.calculated_worker_cost

    @property
    def platform_fee(self):
        subtotal = self.total_cost
        if subtotal is None:
            return Decimal("0.000")
        # Ensure PLATFORM_FEE_PERCENTAGE is a Decimal
        fee_percent = Decimal(str(Config.PLATFORM_FEE_PERCENTAGE))
        return (subtotal * fee_percent) / Decimal("100")

    @property
    def total_estimated_budget(self):
        return self.total_cost + self.platform_fee

    # @property
    # def calculated_reviewer_cost(self):
    #     try:
    #         units = self.task.estimation_config.total_units
    #         redundancy = self.task.config.reviewers_per_task
    #         return units * Decimal(redundancy) * self.reviewer_reward_per_task
    #     except Exception:
    #         return Decimal(0)
