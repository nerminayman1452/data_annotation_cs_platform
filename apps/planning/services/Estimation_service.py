from datetime import datetime, time
from typing import List, Dict, Any, Optional, Type, TypeVar, Union
from django.utils.timezone import make_aware
from django.db import models

from apps.helpers.safe_dev import safe_div
from apps.planning.services.estimation_dto import PlanEstimationDTO
from apps.project_management.models.batch import Batch, Batch
from apps.project_management.models.image_plan import ImagePlan
from apps.project_management.models.project import Project
from apps.project_management.models.text_plan import TextPlan

# Type variable for batch models
BatchModel = TypeVar('BatchModel', bound=models.Model)

class BatchEstimationService:
    """
    Service for managing project estimations based on batch types.
    Handles different batch types (Image, Text, etc.) and provides aggregated estimation data.
    """

    # Define batch models and their display names
    PLAN_TYPES = {
        'image': {
            'model': ImagePlan,
            'name': 'Image Plan',
            'config_relation':'plan_config'
        },
        'text': {
            'model': TextPlan,
            'name': 'Text Plan',
            'config_relation':'config'
        },
        # 'audio': {
        #     'model': AudioPlan,
        #     'name': 'Audio Plan'
        # },
    }

    @classmethod
    def get_batch_estimations(cls, batch_id: int) -> Dict[str, Any]:
        """
        Get estimations for all plans in a batch, grouped by plan type.
        
        Args:
            batch_id: ID of the batch to get estimations for
            
        Returns:
            Dictionary containing batch estimations and summary
        """
        batch = Batch.objects.get(id=batch_id)
        
        plan_results = []
        
        # ---- Aggregated metrics ----
        metrics = {
            'total_cost': 0,
            'total_efforts': 0,
            'total_duration_days': 0,
            'total_duration_weeks': 0,
            'total_actual_workers': 0,
            'workers_per_task': 0,
            'start_dates': [],
            'end_dates': [],
            'plan_counts': {plan_type: 0 for plan_type in cls.PLAN_TYPES}
        }

        # Process each plan type
        for plan_type, config in cls.PLAN_TYPES.items():
            plan_model = config['model']

            active_plans = plan_model.objects.filter(
                batch=batch
            ).select_related("batch").prefetch_related("config", "estimation_config", "cost_config")

            # Process each plan of this type
            for plan in active_plans:
                dto = PlanEstimationDTO(plan)
                plan_data = dto.to_dict()
                
                # Add plan type information
                plan_data.update({
                    # 'plan_type': plan_type,
                    'plan_type_display': config['name'],
                    'id': plan.id,
                    'name': plan.name,
                    'is_approved': getattr(plan, 'cost_config', None) and getattr(plan.cost_config, 'is_approved', False),
                    'is_locked': plan.is_locked,
                })

                plan_results.append(plan_data)
                
                # Update metrics
                metrics['total_cost'] += plan_data.get("total_estimated_budget", 0)
                metrics['total_efforts'] += plan_data.get("effort", 0)
                metrics['total_duration_days'] += plan_data.get("duration_days", 0)
                metrics['total_duration_weeks'] += plan_data.get("duration_weeks", 0)
                # Use .get to avoid KeyError when a plan doesn't expose the field
                metrics['workers_per_task'] += plan_data.get("workers_per_task", 0)
                # Aggregate actual workforce into `total_actual_workers` for summary consistency
                metrics['total_actual_workers'] += plan_data.get("total_workforce", 0)
                
                if dto.start_date:
                    metrics['start_dates'].append(dto.start_date)
                
                if dto.end_date:
                    metrics['end_dates'].append(dto.end_date)
                
                metrics['plan_counts'][plan_type] += 1

        # Calculate summary
        total_plans = len(plan_results)
        
        return {
            'plans': plan_results,
            'summary': cls._generate_summary(metrics, total_plans)
        }

    @classmethod
    def _generate_summary(cls, metrics: Dict[str, Any], total_plans: int) -> Dict[str, Any]:
        """Generate summary statistics from metrics."""
        # Date calculations
        total_start_date = min(metrics['start_dates']) if metrics['start_dates'] else None
        total_end_date = max(metrics['end_dates']) if metrics['end_dates'] else None
        
        avg_start_date = cls._average_date(metrics['start_dates'])
        avg_end_date = cls._average_date(metrics['end_dates'])
        
        # Convert dates to ISO strings so JSON renderer can encode them safely
        def _iso(d):
            try:
                return d.isoformat() if d is not None else None
            except Exception:
                return d

        return {
            'total_plans': total_plans,
            'plan_type_counts': metrics['plan_counts'],
            
            # Cost metrics
            'total_cost': round(metrics['total_cost'], 2),
            'avg_cost_per_plan': round(safe_div(metrics['total_cost'], total_plans), 2),
            
            # Duration metrics
            'total_duration_days': round(metrics['total_duration_days'], 2),
            'avg_duration_per_plan_days': round(
                safe_div(metrics['total_duration_days'], total_plans), 2
            ),
            'total_duration_weeks': round(metrics['total_duration_weeks'], 2),
            'avg_duration_per_plan_weeks': round(
                safe_div(metrics['total_duration_weeks'], total_plans), 2
            ),
            
            # Workforce metrics
            'avg_workers_per_plan': round(
                safe_div(metrics['total_actual_workers'], total_plans), 2
            ) if total_plans > 0 else 0,
            
            'total_actual_workers': metrics['total_actual_workers'],
            'avg_actual_workers_per_plan': round(
                safe_div(metrics['total_actual_workers'], total_plans), 2
            ) if total_plans > 0 else 0,
            
            # Effort metrics
            'total_efforts': round(metrics['total_efforts'], 2),
            'avg_efforts_per_plan': round(
                safe_div(metrics['total_efforts'], total_plans), 2
            ) if total_plans > 0 else 0,
            
            # Timeline metrics (ISO strings)
            'total_start_date': _iso(total_start_date),
            'total_end_date': _iso(total_end_date),
            'avg_start_date': _iso(avg_start_date),
            'avg_end_date': _iso(avg_end_date),
        }

    @staticmethod
    def _average_date(dates: List[datetime]) -> Optional[datetime]:
        """
        Calculate the average (mean) date from a list of date or datetime objects.
        
        Args:
            dates: List of date or datetime objects
            
        Returns:
            Average datetime as a timezone-aware datetime, or None if input is empty
        """
        if not dates:
            return None

        datetimes = []

        for d in dates:
            # If it's a date (no time component), convert to datetime at start of day
            if hasattr(d, "year") and not hasattr(d, "hour"):
                dt = datetime.combine(d, time.min)
            else:
                dt = d

            # Ensure datetime is timezone-aware
            if dt.tzinfo is None:
                dt = make_aware(dt)
            datetimes.append(dt)

        # Calculate average timestamp
        timestamps = [dt.timestamp() for dt in datetimes]
        avg_timestamp = sum(timestamps) / len(timestamps)
        
        # Convert back to datetime and ensure timezone awareness
        avg_dt = datetime.fromtimestamp(avg_timestamp)
        if datetimes and datetimes[0].tzinfo:
            avg_dt = make_aware(avg_dt, timezone=datetimes[0].tzinfo)
            
        return avg_dt
