from dataclasses import dataclass
from typing import List, Optional, Tuple
from datetime import datetime

from apps.dashboard.helpers.plan_utils import PlanInspector
from django.db import models


@dataclass
class UserStats:
    """Container for user's gamification stats"""
    xp_points: int = 0
    datcoins: float = 0.0
    level: int = 1
    accuracy: float = 0.0

    @property
    def next_level_xp(self) -> int:
        """XP needed for next level, using a simple progression"""
        return self.level * 1000  # each level needs level*1000 XP

    @property
    def level_progress(self) -> float:
        """Progress towards next level as percentage"""
        next_xp = self.next_level_xp
        current_level_xp = (self.level - 1) * 1000
        level_xp = self.xp_points - current_level_xp
        return min(100.0, (level_xp / (next_xp - current_level_xp)) * 100)


class UserStatsCalculator:
    """
    Calculates user statistics (XP, coins, level) based on their annotation history.
    Uses a simple but engaging progression system:
    - XP: earned for completing tasks and maintaining accuracy
    - Coins: earned for validated contributions
    - Levels: milestone-based progression (every 1000 XP)
    """

    # Base rewards
    XP_PER_TASK = 10

    #todo based on config 
    COINS_PER_TASK = 5  # fallback if no reward_per_task configured (units: datcoins)
    
    # Bonuses
    ACCURACY_XP_BONUS = 5  # bonus XP per task when accuracy > 90%
    SPEED_COINS_BONUS = 2  # bonus coins for completing before deadline
    
    @classmethod
    def calculate_stats(cls, member_id: int, plan_model_tuples: Optional[List[Tuple]] = None) -> UserStats:
        """Calculate complete stats for a user across all annotation types.

        plan_model_tuples: list of (plan_model, task_model, annotation_model). If not
        provided, PlanInspector.get_plan_models() will be used.
        """
        stats = UserStats()

        total_tasks = 0
        correct_tasks = 0
        accepted_count_total = 0
        completed_before_deadline = 0

        if plan_model_tuples is None:
            plan_model_tuples = PlanInspector.get_plan_models()

        for _, task_model, annotation_model in plan_model_tuples:
            if not annotation_model:
                continue

            try:
                # fetch annotations for this annotator; annotator FK name varies by project
                # we keep existing convention and filter by annotator_id
                qs_all = annotation_model.objects.filter(annotator_id=member_id)
                # eager load related task and plan to avoid N+1
                qs_all = qs_all.select_related("task", "task__plan", "task__plan__plan_config")

                # tasks considered for XP and accuracy are submitted or accepted
                qs_considered = qs_all.filter(status__in=["accepted", "submitted"])
                task_count = qs_considered.count()
                total_tasks += task_count

                # Determine if this annotation model supports 'is_correct' field
                supports_is_correct = False
                try:
                    # will raise if field not present
                    annotation_model._meta.get_field("is_correct")
                    supports_is_correct = True
                except Exception:
                    supports_is_correct = False

                # Count correct/accurate annotations when the model provides 'is_correct'
                if supports_is_correct:
                    try:
                        correct_count = qs_considered.filter(is_correct=True).count()
                    except Exception:
                        correct_count = 0
                    correct_tasks += correct_count

                # Calculate datcoins only for accepted (approved) annotations using reward_per_task
                accepted_qs = qs_all.filter(status="accepted")
                # iterate accepted annotations to sum configured reward_per_task (plan-level)
                accepted_count = accepted_qs.count()
                accepted_count_total += accepted_count
                if accepted_count:
                    for ann in accepted_qs.iterator():
                        plan = getattr(getattr(ann, "task", None), "plan", None)
                        reward = None
                        try:
                            plan_config = getattr(plan, "plan_config", None)
                            reward = getattr(plan_config, "reward_per_task", None) if plan_config is not None else None
                        except Exception:
                            reward = None

                        if reward is not None:
                            try:
                                stats.datcoins += float(reward)
                            except Exception:
                                # fallback to configured constant if conversion fails
                                stats.datcoins += float(cls.COINS_PER_TASK)
                        else:
                            # fallback when plan doesn't configure reward_per_task
                            stats.datcoins += float(cls.COINS_PER_TASK)

                # For early completions (speed bonus), consider accepted annotations only
                early = 0
                for ann in accepted_qs.iterator():
                    # determine timestamp for completion
                    completed_at = getattr(ann, "updated_at", None) or getattr(ann, "created_at", None)
                    plan = getattr(getattr(ann, "task", None), "plan", None)
                    if not plan or not completed_at:
                        continue

                    duration = PlanInspector.get_plan_duration(plan)
                    deadline = PlanInspector.calculate_deadline(plan, duration)
                    if deadline and completed_at <= deadline:
                        early += 1

                completed_before_deadline += early

            except Exception:
                # on any model error, skip this annotation model
                continue

        # Calculate base XP and coins
        if total_tasks > 0:
            stats.xp_points = total_tasks * cls.XP_PER_TASK

            # Calculate accuracy (prefer explicit is_correct where supported; otherwise use accepted ratio)
            if total_tasks:
                if correct_tasks > 0:
                    stats.accuracy = (correct_tasks / total_tasks) * 100
                elif accepted_count_total > 0:
                    stats.accuracy = (accepted_count_total / total_tasks) * 100
                else:
                    stats.accuracy = 0.0
            else:
                stats.accuracy = 0.0

            if stats.accuracy > 90:
                stats.xp_points += total_tasks * cls.ACCURACY_XP_BONUS

            # Add speed bonus coins (for early accepted annotations)
            stats.datcoins += completed_before_deadline * cls.SPEED_COINS_BONUS

            # Calculate level based on XP
            stats.level = max(1, (stats.xp_points // 1000) + 1)

        return stats