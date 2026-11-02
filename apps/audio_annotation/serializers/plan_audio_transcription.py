from rest_framework import serializers

from apps.audio_annotation.models.plan_audio_labelling import EmotionLabel, PlanLabellingConfig, PlanLabellingConfig, \
    AudioLabellingPlan
from apps.audio_annotation.models.plan_audio_speaker_diarization import SpeakerLabel, PlanSpeakerDiarizationConfig, \
    AudioSpeakerDiarizationPlan
from apps.audio_annotation.models.plan_audio_transcription import PlanTranscriptionConfig, AudioTranscriptionPlan
from apps.project_management.models.batch import Batch




class PlanTranscriptionConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanTranscriptionConfig
        fields = '__all__'


class AudioTranscriptionPlanSerializer(serializers.ModelSerializer):
    plan_transcription_conf_id = PlanTranscriptionConfigSerializer()
    batch = serializers.PrimaryKeyRelatedField(queryset=Batch.objects.all())

    class Meta:
        model = AudioTranscriptionPlan
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

    def validate(self, attrs):
        batch = attrs.get('batch')

        if not batch:
            raise serializers.ValidationError("Batch is required.")

        if batch.created_by != self.context['request'].user:
            raise serializers.ValidationError("You do not have permission to add plans to this batch.")

        if AudioTranscriptionPlan.objects.filter(plan_name=attrs.get('plan_name', '').strip(),
                                            batch=batch.id).exists():
            raise serializers.ValidationError("This plan is created before")

        return attrs

    def create(self, validated_data):
        config_data = validated_data.pop('plan_labelling_conf_id')
        config = PlanTranscriptionConfig.objects.create(**config_data)
        plan = AudioTranscriptionPlan.objects.create(
            plan_labelling_conf_id=config_data,
            **validated_data
        )

        return plan
