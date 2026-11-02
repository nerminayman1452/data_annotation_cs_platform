from rest_framework import serializers

from apps.audio_annotation.models.plan_audio_labelling import PlanLabellingConfig, \
    AudioLabellingPlan
from apps.audio_annotation.models.plan_audio_speaker_diarization import SpeakerLabel, PlanSpeakerDiarizationConfig, \
    AudioSpeakerDiarizationPlan
from apps.project_management.models.batch import Batch

class SpeakerLabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpeakerLabel
        fields = '__all__'


class PlanSpeakerDiarizationConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanSpeakerDiarizationConfig
        fields = '__all__'


class AudioSpeakerDiarizationPlanSerializer(serializers.ModelSerializer):
    plan_speaker_diarization_conf_id = PlanSpeakerDiarizationConfigSerializer()
    Speaker_labels = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=SpeakerLabel.objects.all(),
        required=True
    )
    batch = serializers.PrimaryKeyRelatedField(queryset=Batch.objects.all())

    class Meta:
        model = AudioSpeakerDiarizationPlan
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

    def validate_speaker_labels(self, value):
        if not value:
            raise serializers.ValidationError("At least one speaker label is required")
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
        speaker_labels = validated_data.pop('speaker_labels')
        config = PlanSpeakerDiarizationConfig.objects.create(**config_data)
        plan = AudioSpeakerDiarizationPlan.objects.create(
            plan_labelling_conf_id=config_data,
            **validated_data
        )

        # Add the emotion labels
        plan.speaker_labels.set(speaker_labels)
        return plan
