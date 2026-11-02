from apps.dashboard.helpers.stats import UserStatsCalculator
from apps.dashboard.serializers.dashboard import BatchCardSerializer
from apps.dashboard.services.plan_service import PlanService
from apps.dashboard.helpers.plan_utils import PlanInspector
from apps.dashboard.services.recent_plans import RecentPlansBuilder
from apps.project_management.models.plan_members import PlanMember
from apps.project_management.models.batch import Batch


class DashboardService:
    """Handles dashboard data aggregation for annotators."""

    @staticmethod
    def get_member_id(user_id: int) -> int:
        return PlanMember.objects.filter(profile=user_id).values_list("id", flat=True).first()

    @staticmethod
    def get_user_stats(member_id: int):
        return UserStatsCalculator.calculate_stats(
            member_id=member_id,
            plan_model_tuples=PlanInspector.get_plan_models()
        )

    @staticmethod
    def get_active_batches(request, member_id: int, limit: int = 20):
        active_batches_qs = Batch.objects.filter(
            status__in=["pending", "processing"]
        ).order_by("-updated_at")[:limit]

        serializer = BatchCardSerializer(
            active_batches_qs,
            many=True,
            context={"request": request, "membership": member_id}
        )
        return serializer.data
    
    @staticmethod
    def get_my_active_batches(request, member_id: int, limit: int = 20):
        """
        Return only batches where the user has worked on tasks, and a member in it.
        """
        # Only batches where the user is a member
        batch_ids = PlanMember.objects.filter(id=member_id).values_list("batch_id", flat=True)
        
        active_batches_qs = Batch.objects.filter(
            id__in=batch_ids,
            status__in=["pending", "processing"]
        ).order_by("-updated_at")[:limit]

        serializer = BatchCardSerializer(
            active_batches_qs,
            many=True,
            context={"request": request, "membership": member_id}
        )
        return serializer.data

    @staticmethod
    def get_recent_plans(member_id: int, limit_per_model: int = 10, top_n: int = 10):
        plan_models = [pm for pm, _, _ in PlanInspector.get_plan_models()]
        builder = RecentPlansBuilder(member_id=member_id, limit_per_model=limit_per_model)
        recent_plans = builder.build(plan_models)
        return recent_plans[:top_n]
    
    @staticmethod
    def get_my_recent_plans(member_id: int, limit_per_model: int = 10, top_n: int = 10):
        plan_models = [pm for pm, _, _ in PlanInspector.get_plan_models()]
        builder = RecentPlansBuilder(member_id=member_id, limit_per_model=limit_per_model)

        # Build all plans
        recent_plans = builder.build(plan_models)

        # Only keep plans where the user is a member of the batch
        user_batch_ids = PlanMember.objects.filter(id=member_id).values_list("batch_id", flat=True)
        recent_plans = [p for p in recent_plans if p.get("batch_id") in user_batch_ids]

        return recent_plans[:top_n]
