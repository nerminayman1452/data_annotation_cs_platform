from typing import List, Optional
from apps.dashboard.services.plan_service import PlanService


class RecentPlansBuilder:
    """Builds a list of recent plans including both total and per-annotator completed counts.

    Responsibilities:
    - Query recent plans for a set of plan models
    - Compute tasks_count, total_submitted_count and my_completed_count
    - Compute deadline and days_remaining
    """

    def __init__(self, member_id: Optional[int] = None, limit_per_model: int = 10):
        self.member_id = member_id
        self.limit_per_model = limit_per_model

    def build(self, plan_models: List[type]) -> List[dict]:
        results = []
        # build quick map from plan model -> (task_model, annotation_model)
        plan_model_map = {pm: (tm, am) for pm, tm, am in PlanService.get_plan_models()}

        for pm in plan_models:
            try:
                qs = pm.objects.order_by("-created_at")[: self.limit_per_model]
            except Exception:
                continue

            for p in qs:
                task_model, annotation_model = plan_model_map.get(pm, (None, None))
                tasks_count, completed_count = PlanService.count_tasks_and_completed(p, task_model, annotation_model)

                my_completed_count = 0
                if annotation_model and self.member_id:
                    try:
                        my_completed_count = annotation_model.objects.filter(
                            task__plan=p,status__in=["submitted","accepted","rejected","under_review"], annotator_id=self.member_id
                        ).count()
                    except Exception:
                        my_completed_count = 0

                duration = PlanService.get_plan_duration(p)
                deadline = PlanService.calculate_deadline(p, duration)
                days_remaining = PlanService.days_remaining(deadline)

                results.append(
                    {
                        "id": getattr(p, "id", None),
                        "plan_name": getattr(p, "plan_name", None),
                        "batch_id": getattr(p, "batch_id", None) or (getattr(p, "batch", None) and getattr(p.plan, "id", None)),
                        "type": pm.__name__,
                        "created_at": getattr(p, "created_at", None),
                        "deadline": deadline.isoformat() if deadline else None,
                        "days_remaining": days_remaining,
                        "tasks_count": tasks_count,
                        "total_submitted_count": completed_count,
                        "my_completed_count": my_completed_count,
                    }
                )

        # sort combined list and take top overall recent
        try:
            results.sort(key=lambda x: x.get("created_at") or 0, reverse=True)
        except Exception:
            pass

        return results
