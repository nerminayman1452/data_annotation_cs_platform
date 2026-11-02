from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.audio_annotation.models.plan_audio_segmentation import AudioSegmentationPlan
from apps.project_management.models.batch import Batch

class AudioSegmentationPlanSerializer(serializers.ModelSerializer):
    batch = serializers.PrimaryKeyRelatedField(queryset=Batch.objects.all(), write_only=True, required=True)

    class Meta:
        model = AudioSegmentationPlan
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_plan_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Plan name must not be empty.")
        return value

    def validate(self, data):
        request_user = self.context['request'].user
        plan_name = data.get('plan_name')
        batch = data.get('batch')

        if not batch:
            raise serializers.ValidationError("Batch must be provided.")

        if batch.created_by != request_user:
            raise serializers.ValidationError("Only the batch owner can create a plan for this batch.")

        if AudioSegmentationPlan.objects.filter(plan_name=plan_name, batch=batch).exists():
            raise serializers.ValidationError(f"Plan '{plan_name}' already exists for this batch.")

        return data

    def create(self, validated_data):
        return AudioSegmentationPlan.objects.create(**validated_data)
