from rest_framework import serializers

from apps.project_management.models.batch import Batch
from apps.project_management.models.text_plan import TextPlanRawData
# from apps.project_management.models.batch import Batchfrom apps.project_management.models.text_batch_data import TextBatchData
# from apps.text_annotation.models.plan_text_segmentation import TextSegmentationPlan
from apps.text_annotation.models.task_text_segmentation import TextSegmentationTaskResult


class TextSegmentationTaskResultSerializer(serializers.ModelSerializer):
    batch_data = serializers.PrimaryKeyRelatedField(
        queryset=TextPlanRawData.objects.all(),
        required=False,
        allow_null=True
    )
    batch = serializers.PrimaryKeyRelatedField(
        queryset=Batch.objects.all(),
    )

    # plan_segmentation = serializers.PrimaryKeyRelatedField(
    #     queryset=TextSegmentationPlan.objects.all()
    # )

    class Meta:
        model = TextSegmentationTaskResult
        fields = [
            "id",
            "batch",
            "batch_data",
            "plan_segmentation",
            "phase_index",
            "segmentation_result",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs):
        batch = attrs.get("batch")
        batch_data = TextPlanRawData.objects.filter(batch_id=batch.id).exists()

        # Permission check for the batch
        if batch.created_by != self.context['request'].user:
            raise serializers.ValidationError("You do not have permission to generate tasks for this batch.")

        # Check if there is batch data
        if not batch_data:
            raise serializers.ValidationError("No batch data found for the selected batch.")


        return attrs