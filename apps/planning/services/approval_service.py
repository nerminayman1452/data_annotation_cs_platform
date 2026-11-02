from django.utils import timezone

from apps.planning.services.Estimation_service import BatchEstimationService


class BatchApprovalService:

    @staticmethod
    def approve(batch, user):
        if batch.is_approved:
            return

        # Freeze all configs
        for model in BatchEstimationService.PLAN_MODELS:
            for plan in model.objects.filter(batch=batch):
                config = plan.get_config()
                config.is_approved = True
                config.approved_at = timezone.now()
                config.save(update_fields=[
                     "is_approved", "approved_at"
                ])

        batch.is_approved = True
        # batch.is_active = 
        batch.approved_at = timezone.now()
        batch.save()
