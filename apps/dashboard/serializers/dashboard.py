from apps.project_management.models.image_plan import ImagePlan
from rest_framework import serializers
from apps.project_management.models.plan_members import PlanMember
from apps.dashboard.helpers.batch_access_manager import BatchAccessManager
from apps.dashboard.helpers.plan_utils import PlanInspector
# from apps.image_annotation.models.task_img_classification import ImageClassificationAnnotation

PlanUtils = PlanInspector


class PlanSummarySerializer(serializers.ModelSerializer):
    tasks_count = serializers.IntegerField()
    completed_count = serializers.IntegerField()
    my_progress = serializers.SerializerMethodField()

    class Meta:
        model = ImagePlan
        fields = ("id", "plan_name", "plan_description", "tasks_count", "completed_count", "my_progress")

    def get_my_progress(self, obj):
        membership = self.context.get("membership")
        if not membership:
            return None
        # return ImageClassificationAnnotation.objects.progress_for_annotator(membership, obj.id)
        return None


class BatchCardSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source="project.name", read_only=True)
    plans = serializers.SerializerMethodField()
    members_count = serializers.SerializerMethodField()
    access_status = serializers.SerializerMethodField() 

    class Meta:
        model = ImagePlan
        fields = (
            "id",
            "name",
            "project_name",
            "status",
            "plans",
            "members_count",
            "access_status",
        )

    def get_access_status(self, obj):
        """Return the access status of the current user for this batch."""
        request = self.context.get("request")
        user_id = getattr(request.user, "id", None)
        if not user_id:
            return "unknown"
        return BatchAccessManager.get_access_status(obj, user_id)

    def get_plans(self, obj):
        """Return all plans related to this batch with progress info."""
        results = []
        for plan_model, task_model, annotation_model in PlanUtils.get_plan_models():
            try:
                qs = plan_model.objects.filter(batch=obj)
            except Exception:
                continue

            membership = self.context.get("membership")
            for p in qs:
                tasks_count, completed_count = PlanUtils.count_tasks_and_completed(p, task_model, annotation_model)

                my_completed_count = 0
                my_approved_count = 0
                my_rejected_count = 0
                if annotation_model and membership:
                    try:
                        my_completed_count = annotation_model.objects.filter(
                            task__plan=p,
                            status__in=["submitted","accepted","rejected","under_review"],
                            annotator_id=membership,
                        ).count()
                        my_approved_count = annotation_model.objects.filter(
                            task__plan=p,
                            status="accepted",
                            annotator_id=membership,
                        ).count()
                        my_rejected_count = annotation_model.objects.filter(
                            task__plan=p,
                            status="rejected",
                            annotator_id=membership,
                        ).count()
                    except Exception:
                        pass

                duration = PlanUtils.get_plan_duration(p)
                deadline = PlanUtils.calculate_deadline(p, duration)
                days_remaining = PlanUtils.days_remaining(deadline)

                results.append({
                    "id": p.id,
                    "plan_name": getattr(p, "plan_name", str(p)),
                    "type": plan_model.__name__,
                    "tasks_count": tasks_count,
                    "total_submitted_count": completed_count,
                    "my_completed_count": my_completed_count,
                    "my_approved_count": my_approved_count,
                    "my_rejected_count": my_rejected_count,
                    "days_remaining": days_remaining,
                    "created_at": getattr(p, "created_at", None).isoformat() if getattr(p, "created_at", None) else None,
                })

        results.sort(key=lambda x: x.get("created_at") or "", reverse=True)
        return results

    def get_members_count(self, obj):
        """Return count of annotators in this batch."""
        return PlanMember.objects.filter(batch=obj, user_role="Annotator").count()
