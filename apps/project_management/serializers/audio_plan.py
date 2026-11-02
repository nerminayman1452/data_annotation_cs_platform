from rest_framework import serializers
from django.db import transaction

from apps.planning.models.measure_unit import MeasureUnits
from apps.project_management.models.batch import Batch
from apps.project_management.models.audio_plan import (
    AudioPlan, AudioPlanConfig, AudioPlanCostConfig, 
    AudioPlanEstimationConfig, EmotionLabel, SpeakerLabel, 
    AudioPlanStatusHistory
)
from apps.project_management.serializers.plan import PlanResponseMixin


class EmotionLabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmotionLabel
        fields = '__all__'


class SpeakerLabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpeakerLabel
        fields = '__all__'


class AudioPlanCostConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = AudioPlanCostConfig
        fields = ['cost_per_unit', 'is_approved', 'approved_at']
        read_only_fields = ['approved_at']


class AudioPlanEstimationConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = AudioPlanEstimationConfig
        fields = ['start_date', 'has_auto_progress', 'total_units', 'duration', 'duration_unit', 'measure_unit']


class AudioPlanConfigSerializer(serializers.ModelSerializer):
    emotion_labels = serializers.PrimaryKeyRelatedField(
        queryset=EmotionLabel.objects.all(), many=True, required=False
    )
    speaker_labels = serializers.PrimaryKeyRelatedField(
        queryset=SpeakerLabel.objects.all(), many=True, required=False
    )

    class Meta:
        model = AudioPlanConfig
        fields = [
            'config', 'workers_per_task', 'task_distribution_mode', 'standard',
            'time_per_task', 'acceptance_agreement', 'emotion_labels', 
            'speaker_labels', 'maximum_segment_duration'
        ]


class AudioPlanSerializer(PlanResponseMixin, serializers.ModelSerializer):
    # Cost Config
    cost_per_unit = serializers.DecimalField(
        required=False, 
        source='cost_config.cost_per_unit', 
        max_digits=10, 
        decimal_places=3
    )
    is_approved = serializers.BooleanField(required=False, source='cost_config.is_approved')
    
    # Estimation Config
    start_date = serializers.DateField(required=False, source='estimation_config.start_date')
    has_auto_progress = serializers.BooleanField(required=False, source='estimation_config.has_auto_progress')
    duration = serializers.IntegerField(required=False, source='estimation_config.duration')
    duration_unit = serializers.CharField(required=False, source='estimation_config.duration_unit')
    measure_unit = serializers.PrimaryKeyRelatedField(
        queryset=MeasureUnits.objects.all(),
        required=False,
        source='estimation_config.measure_unit',
        allow_null=True
    )
    total_units = serializers.IntegerField(required=False, source='estimation_config.total_units')

    # Plan Config
    config = serializers.JSONField(required=False, source='config.config')
    workers_per_task = serializers.IntegerField(required=False, source='config.workers_per_task')
    task_distribution_mode = serializers.CharField(required=False, source='config.task_distribution_mode')
    standard = serializers.FloatField(required=False, source='config.standard')
    time_per_task = serializers.IntegerField(required=False, source='config.time_per_task')
    acceptance_agreement = serializers.IntegerField(required=False, source='config.acceptance_agreement')
    maximum_segment_duration = serializers.IntegerField(
        required=False, source='config.maximum_segment_duration'
    )
    
    emotion_labels = serializers.PrimaryKeyRelatedField(
        queryset=EmotionLabel.objects.all(), 
        many=True, 
        required=False, 
        source='config.emotion_labels'
    )
    speaker_labels = serializers.PrimaryKeyRelatedField(
        queryset=SpeakerLabel.objects.all(), 
        many=True, 
        required=False, 
        source='config.speaker_labels'
    )
    
    batch = serializers.PrimaryKeyRelatedField(
        queryset=Batch.objects.all(), 
        required=False, 
        allow_null=True, 
        write_only=True
    )

    class Meta:
        model = AudioPlan
        fields = [
            # Main Fields
            'id', 'title', 'description', 'name', 'annotation_type', 'is_locked', 'batch',
            'created_by', 'status', 'created_at', 'updated_at',
            
            # Flattened Config Fields
            'cost_per_unit', 'is_approved',
            'start_date', 'duration', 'duration_unit', 'measure_unit', 'total_units',
            'config', 'workers_per_task', 'task_distribution_mode', 'standard', 'time_per_task',
            'acceptance_agreement', 'maximum_segment_duration', 'emotion_labels', 'speaker_labels',

            # Calculated/Read-Only Mixin Fields
            'batch_name', 'project_title', 'organization_title', 'batch_id', 
            'rates', 'efforts', 'task_cost', 'platform_fee', 'total_estimated_budget', 
            'end_date', 'actual_end_date', 'duration_days', 'duration_weeks',
            'actual_units', 'progress', 'progress_till_now', 'weight', 'weight_times_progress',
            'quality', 'workers', 'has_auto_progress', 'is_actual', 'actual_plan_detail',
        ]
        read_only_fields = ['status', 'created_at', 'updated_at', 'is_approved']

    def validate(self, attrs):
        batch = attrs.get('batch')
        if batch:
            is_owner = Batch.objects.filter(id=batch.id, created_by=int(self.context['request'].user.id)).exists()
            if not is_owner:
                raise serializers.ValidationError("You do not have permission to add plans to this batch.")
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        # Extract nested data
        cost_data = {}
        est_data = {}
        config_data = {}
        
        raw_config = validated_data.pop('config', {})
        raw_cost = validated_data.pop('cost_config', {})
        raw_est = validated_data.pop('estimation_config', {})

        # Cost data
        if 'cost_per_unit' in raw_cost: 
            cost_data['cost_per_unit'] = raw_cost['cost_per_unit']
        
        # Estimation data
        for k in ['start_date', 'has_auto_progress', 'duration', 'duration_unit', 'total_units']:
             if k in raw_est: 
                 est_data[k] = raw_est[k]

        if 'measure_unit' in raw_est: 
            est_data['measure_unit_id'] = raw_est['measure_unit'].id if raw_est['measure_unit'] else None

        # Config data
        for k in ['workers_per_task', 'task_distribution_mode', 'standard', 'time_per_task', 
                  'acceptance_agreement', 'maximum_segment_duration']:
             if k in raw_config: 
                 config_data[k] = raw_config[k]
        
        if 'config' in raw_config: 
            config_data['config'] = raw_config['config']

        # Handle M2M fields
        emotion_labels = validated_data.pop('emotion_labels', None)
        speaker_labels = validated_data.pop('speaker_labels', None)

        # Set user
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            validated_data['created_by'] = int(request.user.id)

        # Create plan
        plan = AudioPlan.objects.create(**validated_data)

        # Create related configs
        AudioPlanCostConfig.objects.create(plan=plan, **cost_data)
        AudioPlanEstimationConfig.objects.create(plan=plan, **est_data)
        
        config_instance = AudioPlanConfig.objects.create(plan=plan, **config_data)

        # Set M2M relations
        if emotion_labels:
            config_instance.emotion_labels.set(emotion_labels)
        if speaker_labels:
            config_instance.speaker_labels.set(speaker_labels)

        return plan


class AudioPlanStatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = AudioPlanStatusHistory
        fields = ['id', 'plan', 'status', 'started_at', 'ended_at']
