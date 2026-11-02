from apps.project_management.models.batch import Batch
# from apps.text_annotation.models.plan_text_labelling import PlanLabellingConfig
from rest_framework import serializers

from apps.audio_annotation.models.plan_audio_labelling import EmotionLabel, AudioPlanLabellingConfig,  \
    AudioLabellingPlan
# from apps.project_management.models.batch import Batch

class EmotionLabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmotionLabel
        fields = '__all__'


class PlanLabellingConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = AudioPlanLabellingConfig
        fields = '__all__'


class AudioLabellingPlanSerializer(serializers.ModelSerializer):
    plan_labelling_conf_id = PlanLabellingConfigSerializer()
    emotion_labels = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=EmotionLabel.objects.all(),
        required=True
    )
    batch = serializers.PrimaryKeyRelatedField(queryset=Batch.objects.all())

    class Meta:
        model = AudioLabellingPlan
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

    def validate_emotion_labels(self, value):
        if not value:
            raise serializers.ValidationError("At least one emotion label is required")
        return value

    def validate(self, attrs):
        batch = attrs.get('batch')

        if not batch:
            raise serializers.ValidationError("Batch is required.")

        if batch.created_by != self.context['request'].user:
            raise serializers.ValidationError("You do not have permission to add plans to this batch.")

        if AudioLabellingPlan.objects.filter(plan_name=attrs.get('plan_name', '').strip(),
                                            batch=batch.id).exists():
            raise serializers.ValidationError("This plan is created before")

        return attrs

    def create(self, validated_data):
        config_data = validated_data.pop('plan_labelling_conf_id')
        emotion_labels = validated_data.pop('emotion_labels')
        config = AudioPlanLabellingConfig.objects.create(**config_data)
        plan = AudioLabellingPlan.objects.create(
            plan_labelling_conf_id=config_data,
            **validated_data
        )

        # Add the emotion labels
        plan.emotion_labels.set(emotion_labels)
        return plan
