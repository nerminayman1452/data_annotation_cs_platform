from rest_framework import serializers

from apps.tasks.serializers.plan_task import BasePlanTaskSerializer
from apps.text_annotation.models import TextPlanTask


class TextPlanTaskSerializer(BasePlanTaskSerializer):
    class Meta(BasePlanTaskSerializer.Meta):
        model = TextPlanTask
        fields = BasePlanTaskSerializer.Meta.fields + [
            "plan",
            "plan_file",
            "members",
        ]

class GenerateTextTasksSerializer(serializers.Serializer):
    plan_id = serializers.IntegerField()
