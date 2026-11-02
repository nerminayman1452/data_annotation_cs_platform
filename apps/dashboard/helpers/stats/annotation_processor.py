from typing import Optional
from datetime import datetime
from ..plan_utils import PlanInspector

class AnnotationProcessor:
    """Processes annotation data to extract metrics and statistics"""
    
    @staticmethod
    def check_early_completion(annotation, plan) -> bool:
        """Check if an annotation was completed before deadline"""
        completed_at = getattr(annotation, "updated_at", None) or getattr(annotation, "created_at", None)
        if not plan or not completed_at:
            return False
            
        duration = PlanInspector.get_plan_duration(plan)
        deadline = PlanInspector.calculate_deadline(plan, duration)
        return bool(deadline and completed_at <= deadline)
    
    @staticmethod
    def supports_correctness_check(annotation_model) -> bool:
        """Check if annotation model supports correctness checking"""
        try:
            annotation_model._meta.get_field("is_correct")
            return True
        except Exception:
            return False
            
    @staticmethod
    def get_plan_config(annotation) -> Optional:
        """Extract plan configuration from annotation"""
        try:
            plan = getattr(getattr(annotation, "task", None), "plan", None)
            return getattr(plan, "plan_config", None) if plan else None
        except Exception:
            return None