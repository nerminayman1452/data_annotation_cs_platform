from typing import List, Optional, Tuple
from django.db import models

from .user_stats import UserStats
from .level_manager import LevelManager
from .reward_calculator import RewardCalculator
from .annotation_processor import AnnotationProcessor
from ..plan_utils import PlanInspector

class UserStatsCalculator:
    """Calculates user statistics based on their annotation history"""
    
    # Base rewards
    XP_PER_TASK = 10
    ACCURACY_XP_BONUS = 5
    
    @classmethod
    def calculate_stats(cls, member_id: int, plan_model_tuples: Optional[List[Tuple]] = None) -> UserStats:
        """Calculate complete stats for a user across all annotation types"""
        stats = UserStats()
        if plan_model_tuples is None:
            plan_model_tuples = PlanInspector.get_plan_models()
        
        total_tasks = correct_tasks = accepted_count = early_completions = 0
        all_submitted = all_approved = all_rejected = 0
        
        for _, task_model, annotation_model in plan_model_tuples:
            if not annotation_model:
                continue
            try:
                results = cls._process_annotation_type(member_id, annotation_model)
                
                total_tasks += results['total']
                correct_tasks += results['correct']
                accepted_count += results['accepted']
                early_completions += results['early']
                
                all_submitted += results.get('submitted', 0)
                all_approved += results.get('approved', 0)
                all_rejected += results.get('rejected', 0)
                
                stats.datcoins += results['coins']
            except Exception:
                continue
        
        stats.all_tasks = total_tasks
        stats.all_submitted = all_submitted
        stats.all_approved = all_approved
        stats.all_rejected = all_rejected
        
        if total_tasks > 0:
            stats.accuracy = cls._calculate_accuracy(total_tasks, correct_tasks, accepted_count)
            stats.xp_points = LevelManager.calculate_xp_for_tasks(
                total_tasks, stats.accuracy, cls.XP_PER_TASK, cls.ACCURACY_XP_BONUS
            )
            stats.datcoins += RewardCalculator.calculate_speed_bonus(early_completions)
            stats.level = LevelManager.calculate_level(stats.xp_points)
            
        return stats
    
    @classmethod
    def _process_annotation_type(cls, member_id: int, annotation_model) -> dict:
        """Process annotations of a specific type and return metrics"""
        results = {'total': 0, 'correct': 0, 'accepted': 0, 'early': 0, 'coins': 0.0,
                   'submitted': 0, 'approved': 0, 'rejected': 0}
        
        
        # Get all annotations for this member
        qs_all = annotation_model.objects.filter(annotator_id=member_id)
        qs_all = qs_all.select_related("task", "task__plan", "task__plan__plan_config")
        
        results['submitted'] = qs_all.filter(status="submitted").count()
        results['approved'] = qs_all.filter(status="accepted").count()
        results['rejected'] = qs_all.filter(status="rejected").count()
        results['total'] = qs_all.filter(status__in=["submitted", "accepted", "rejected"]).count() # total tasks = all submitted/accepted/rejected
        
        if AnnotationProcessor.supports_correctness_check(annotation_model):
            results['correct'] = qs_all.filter(is_correct=True).count()
        
        # Calculate coins and early completions
        for ann in qs_all.filter(status="accepted").iterator():
            plan_config = AnnotationProcessor.get_plan_config(ann)
            results['coins'] += RewardCalculator.calculate_task_reward(plan_config)
            plan = getattr(getattr(ann, "task", None), "plan", None)
            if AnnotationProcessor.check_early_completion(ann, plan):
                results['early'] += 1
                
        results['accepted'] = results['approved']
        return results
    
    @staticmethod
    def _calculate_accuracy(total: int, correct: int, accepted: int) -> float:
        """Calculate accuracy percentage based on available metrics"""
        if total == 0:
            return 0.0
        if correct > 0:
            return (correct / total) * 100
        if accepted > 0:
            return (accepted / total) * 100
        return 0.0