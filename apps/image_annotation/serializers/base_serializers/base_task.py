from functools import lru_cache
from rest_framework import serializers
from apps.project_management.models.batch import Batch# from apps.project_management.models.image_batch_data import ImageBatchData
from services.auth_service.client import get_user_info


@lru_cache(maxsize=512)
def cached_user_info(profile_id, token):
    return get_user_info(profile_id, token)

class BaseImageTaskSerializer(serializers.ModelSerializer):
    batch = serializers.PrimaryKeyRelatedField(queryset=Batch.objects.all())
    image_url = serializers.SerializerMethodField()

    annotator_count = serializers.SerializerMethodField(read_only=True)
    annotators = serializers.SerializerMethodField(read_only=True)

    # NEW: Expose the Status and Decision Source
    task_status = serializers.CharField(read_only=True)
    accepted_by = serializers.CharField(read_only=True)

    # MUST be provided by subclasses
    annotation_model = None

    def validate(self, attrs):
        request = self.context.get("request")
        batch = attrs.get("batch")

        if not batch:
            raise serializers.ValidationError("Batch is required.")

        if batch.created_by != int(request.user.id):
            raise serializers.ValidationError(
                "You do not have permission to generate tasks for this batch."
            )

        # if not ImageBatchData.objects.filter(batch=batch).exists():
        #     raise serializers.ValidationError("No batch data found for this batch.")

        return attrs

    # ---------- Shared Computed Fields ---------- #

    def get_image_url(self, obj):
        request = self.context.get("request")
        if obj.batch_data and obj.batch_data.file:
            return (
                request.build_absolute_uri(obj.batch_data.file.url)
                if request else obj.batch_data.file.url
            )
        return None

    def get_annotator_count(self, obj):
        return obj.annotations.values("annotator").distinct().count()

    def get_annotators(self, obj):
        if not self.annotation_model:
            return []

        request = self.context.get("request")
        if not request:
            return []

        token = request.headers.get("Authorization", "").split(" ")[-1]
        annotators = {}

        for ann in obj.annotations.select_related("annotator"):
            member = ann.annotator
            if not member:
                continue

            progress = self.annotation_model.objects.progress_for_annotator(
                member=member,
                plan_id=obj.plan_id,
            )

            user_info = cached_user_info(member.profile, token)

            annotators[member.id] = {
                "annotator_id": member.id,
                "name": f"{user_info.get('first_name')} {user_info.get('last_name')}",
                "username":f"{user_info['user'].get('username')}",
                "email":f"{user_info['user'].get('email')}",
                "role": member.user_role,
                "total_assigned": progress["total_assigned"],
                "total_completed": progress["total_completed"],
                "remaining": progress["remaining"],
                "progress_percent": progress["progress_percent"],
            }

        return list(annotators.values())
