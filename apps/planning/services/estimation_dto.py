from typing import Any, Dict, Optional
from datetime import datetime, date
from django.db import models

class PlanEstimationDTO:
    """
    Data Transfer Object for plan estimation data.
    This object is PURE (no DB writes, no serializers).
    """

    def __init__(self, plan: models.Model):
        """
        Initialize with a plan instance.
        
        Args:
            plan: A plan model instance (ImagePlan, TextPlan, etc.)
        """
        config = plan.get_config()
        estimation_config = plan.get_estimation_config()
        cost_config = plan.get_cost_config()
        # --- Identity ---
        self.id = plan.id
        self.name = plan.name
        self.plan_type = plan.__class__.__name__.replace('Plan', '').lower()

        # Normalize annotation_type to a JSON-serializable structure.
        ann = getattr(plan, 'annotation_type', None)
        if ann is None:
            self.annotation_type = None
        elif hasattr(ann, 'id') and hasattr(ann, 'name') and hasattr(ann, 'plan_type'):
            # AnnotationType model instance -> primitive dict
            self.annotation_type = {
                'id': getattr(ann, 'id', None),
                'name': getattr(ann, 'name', None),
                'url': getattr(ann, 'url', None),
                'plan_type': getattr(ann, 'plan_type', None),
                'display': str(ann)
            }
        else:
            # Fallback for other representations (string, choice, etc.)
            self.annotation_type = ann

        # --- Timeline ---
        self.start_date: Optional[date] = getattr(estimation_config, 'start_date', None) if estimation_config else None
        self.end_date: Optional[date] = getattr(estimation_config, 'estimated_end_date', None) if estimation_config else None
        self.duration_days: float = float(getattr(estimation_config, 'duration_days', 0)) if estimation_config else 0.0
        self.duration_weeks: float = float(getattr(estimation_config, 'duration_weeks', 0)) if estimation_config else 0.0

        # --- Quantity ---
        self.measure_unit: Optional[str] = (
            estimation_config.measure_unit.title 
            if estimation_config and hasattr(estimation_config, 'measure_unit') and estimation_config.measure_unit 
            else None
        )
        self.total_units: float = float(getattr(estimation_config, 'total_units', 0)) if estimation_config else 0.0
        self.assignments: float = float(getattr(estimation_config, 'total_assignments', 0)) if estimation_config else 0.0

        # --- Capacity ---
        self.standard: int = getattr(config, 'standard', 0) if config else 0
        self.workers_per_task: int = getattr(config, 'workers_per_task', 1) if config else 1
        # self.reviewers_per_task: int = getattr(config, 'reviewers_per_task', 1)

        # Workforce (from plan members)
        # self.annotator_workforce: int = annotator_workforce() if callable(annotator_workforce := getattr(plan, 'annotator_workforce', lambda: 0)) else annotator_workforce
        # self.reviewer_workforce: int = reviewer_workforce() if callable(reviewer_workforce := getattr(plan, 'reviewer_workforce', lambda: 0)) else reviewer_workforce
        
        self.total_workforce: int = total_workforce() if callable(total_workforce := getattr(plan, 'total_workforce', lambda: 0)) else total_workforce

        # --- Rates ---
        self.rates: float = float(getattr(plan, 'rates', 0))

        # --- Effort ---
        self.effort: float = float(getattr(estimation_config, 'efforts', 0)) if estimation_config else 0.0
        self.effort_per_worker: float = float(getattr(estimation_config, 'efforts_per_worker', 0)) if estimation_config else 0.0

        # --- Cost ---
        self.cost_per_unit: float = float(getattr(cost_config, 'cost_per_unit', 0)) if cost_config else 0.0
        # self.reviewer_reward_per_task: float = float(getattr(config, 'reviewer_reward_per_task', 0))
        # self.worker_cost: float = float(getattr(estimation_config, 'calculated_worker_cost', 0))
        # self.reviewer_cost: float = float(getattr(estimation_config, 'calculated_reviewer_cost', 0))
        self.platform_fee: float = float(getattr(cost_config, 'platform_fee', 0)) if cost_config else 0.0
        self.task_cost: float = float(getattr(cost_config, 'total_cost', 0)) if cost_config else 0.0
        self.total_estimated_budget: float = float(getattr(cost_config, 'total_estimated_budget', 0)) if cost_config else 0.0

        # --- Progress & Status ---
        self.progress: float = float(getattr(plan, 'actual_progress', 0))
        self.progress_till_now: float = float(getattr(plan, 'progress_till_now', 0))
        self.has_auto_progress: bool = bool(getattr(estimation_config, 'has_auto_progress', False))
        self.weight_times_progress: float = float(getattr(plan, 'weighted_progress', 0))
        self.weight: float = float(getattr(plan, 'weight', 0))
        self.status: str = getattr(plan, 'status', 'draft')

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the DTO to a dictionary.
        
        Returns:
            Dict containing all DTO attributes
        """
        return {
            k: v.isoformat() if isinstance(v, (date, datetime)) else v
            for k, v in self.__dict__.items()
        }
