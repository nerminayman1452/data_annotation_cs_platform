from rest_framework import serializers

from apps.tasks.serializers.plan_task import BasePlanTaskSerializer
from apps.image_annotation.models import ImagePlanTask


class ImagePlanTaskSerializer(BasePlanTaskSerializer):
    class Meta(BasePlanTaskSerializer.Meta):
        model = ImagePlanTask
        fields = BasePlanTaskSerializer.Meta.fields + [
            "plan",
            "plan_file",
            "members",
        ]

class GenerateImageTasksSerializer(serializers.Serializer):
    plan_id = serializers.IntegerField()