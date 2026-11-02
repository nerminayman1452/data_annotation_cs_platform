from typing import List, Optional, Tuple
from datetime import timedelta, datetime

from apps.dashboard.helpers.plan_utils import PlanInspector


class PlanService:
    """Encapsulates plan/task/annotation related helpers.

    This class wraps the procedural helpers in `PlanInspector` and provides
    a single-responsibility service for plan-related operations. Keeping a
    thin wrapper ensures backward compatibility while making code more
    testable and easier to inject.
    """

    @staticmethod
    def get_plan_models() -> List[Tuple]:
        return PlanInspector.get_plan_models()

    @staticmethod
    def count_tasks_and_completed(plan, task_model, annotation_model):
        return PlanInspector.count_tasks_and_completed(plan, task_model, annotation_model)

    @staticmethod
    def get_plan_duration(plan) -> Optional[int]:
        return PlanInspector.get_plan_duration(plan)

    @staticmethod
    def calculate_deadline(plan, duration: Optional[int]):
        return PlanInspector.calculate_deadline(plan, duration)

    @staticmethod
    def days_remaining(deadline: Optional[datetime], now: Optional[datetime] = None):
        return PlanInspector.days_remaining(deadline, now)
