from rest_framework import serializers

from apps.audio_annotation.models.plan_audio_segmentation import AudioSegmentationPlan
from apps.audio_annotation.models.task_audio_segmentation import AudioSegmentationTaskResult
from apps.project_management.models.batch import  Batch

from apps.project_management.models.audio_plan import AudioPlanRawData


class AudioSegmentationTaskResultSerializer(serializers.ModelSerializer):
    batch_data = serializers.PrimaryKeyRelatedField(
        queryset=AudioPlanRawData.objects.all(),
        required=False,
        allow_null=True
    )
    batch = serializers.PrimaryKeyRelatedField(
        queryset=Batch.objects.all(),
    )

    plan_segmentation = serializers.PrimaryKeyRelatedField(
        queryset=AudioSegmentationPlan.objects.all()
    )

    class Meta:
        model = AudioSegmentationTaskResult
        fields = '__all__'
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs):
        batch = attrs.get("batch")
        batch_data = AudioPlanRawData.objects.filter(batch_id=batch.id).exists()

        # Permission check for the batch
        if batch.created_by != self.context['request'].user:
            raise serializers.ValidationError("You do not have permission to generate tasks for this batch.")

        # Check if there is batch data
        if not batch_data:
            raise serializers.ValidationError("No batch data found for the selected batch.")

        return attrs
