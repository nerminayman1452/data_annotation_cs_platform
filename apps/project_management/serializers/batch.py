from django.utils.timezone import now
from rest_framework import serializers

from apps.project_management.models.batch import Batch, BatchStatusHistory
from apps.project_management.serializers.text_plan import TextPlanSerializer
from apps.project_management.serializers.image_plan import ImagePlanSerializer
from apps.project_management.serializers.audio_plan import AudioPlanSerializer


class BatchSerializer(serializers.ModelSerializer):
    """
    Read-Only Serializer: Flattens Estimates and Actuals into JSON.
    """
    # Parent Info
    project_title = serializers.CharField(source='project.project_name', read_only=True)

    # --- Financials & Targets (Estimates) ---
    total_cost = serializers.DecimalField(source='estimates.total_cost', max_digits=15, decimal_places=3,
                                          read_only=True, allow_null=True)
    total_units = serializers.IntegerField(source='estimates.total_units', read_only=True, allow_null=True)
    total_assignments = serializers.IntegerField(source='estimates.total_assignments', read_only=True, allow_null=True)
    total_efforts = serializers.DecimalField(source='estimates.total_efforts', max_digits=10, decimal_places=2,
                                             read_only=True, allow_null=True)

    # --- Execution (Actuals) ---
    actual_cost = serializers.DecimalField(source='actuals.total_cost', max_digits=15, decimal_places=3, read_only=True, allow_null=True)
    actual_units = serializers.IntegerField(source='actuals.total_units', read_only=True, allow_null=True)
    progress = serializers.FloatField(source='actuals.progress_percent', read_only=True, allow_null=True)
    quality = serializers.FloatField(source='actuals.quality', read_only=True, allow_null=True)
    time_elapsed_percentage = serializers.FloatField(source='actuals.time_elapsed_percent', read_only=True, allow_null=True)

    # --- Counts ---
    actual_plans_count = serializers.IntegerField(source='actuals.total_plans_count', read_only=True, allow_null=True)
    actual_members = serializers.IntegerField(source='actuals.total_members', read_only=True, allow_null=True)
    actual_plans_types = serializers.ListField(source='actuals.total_plans_types', read_only=True, allow_null=True)

    # --- Timing & Throughput ---
    start_date = serializers.DateField(source='estimates.start_date', read_only=True)
    end_date = serializers.DateField(source='estimates.end_date', read_only=True)
    duration_days = serializers.IntegerField(source='estimates.duration_days', read_only=True)
    duration_weeks = serializers.IntegerField(source='estimates.duration_weeks', read_only=True)
    daily_unit_throughput = serializers.IntegerField(source='estimates.daily_unit_throughput', read_only=True)
    daily_assignment_throughput = serializers.IntegerField(source='estimates.daily_assignment_throughput',
                                                           read_only=True)
    daily_effort = serializers.IntegerField(source='estimates.daily_effort', read_only=True)

    # --- Strategic ---
    weight = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True, allow_null=True)
    weight_times_progress = serializers.DecimalField(source='actuals.weight_times_progress', max_digits=5,
                                                     decimal_places=2, read_only=True, allow_null=True)

    class Meta:
        model = Batch
        fields = [
            'id', 'name', 'project', 'project_title', 'status', 'total_amount',
            'is_approved', 'is_template', 'created_by', 'created_at', 'updated_at',
            # Flattened
            'total_cost', 'total_units', 'total_assignments', 'total_efforts',
            'actual_cost', 'actual_units', 'progress', 'quality',
            'start_date', 'end_date', 'duration_days','duration_weeks', 'time_elapsed_percentage',
            'daily_unit_throughput', 'daily_assignment_throughput','daily_effort',
            'weight', 'weight_times_progress', 'actual_members',
            'actual_plans_types', 'actual_plans_count'
        ]
        read_only_fields = fields


class BatchCreateSerializer(serializers.ModelSerializer):
    """
    Write-Only Serializer: Inputs and Validation only.
    """
    class Meta:
        model = Batch
        fields = ['project', 'name', 'total_amount', 'is_template', 'is_approved']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, attrs):
        request = self.context.get('request')
        project = attrs.get('project')
        name = attrs.get('name')

        # todo (project members) check for ownership of the batch 
        # 1. Ownership Check
        if project and project.organization.created_by != int(request.user.id):
            raise serializers.ValidationError({"project": "You can only create batches for projects you own."})

        # 2. Duplicate Check
        if Batch.objects.filter(project=project, name=name).exists():
            raise serializers.ValidationError({"name": "A batch with this name already exists in this project."})

        return attrs

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user.id
        batch = Batch.objects.create(**validated_data)

        # Init History
        BatchStatusHistory.objects.create(
            batch=batch,
            status=batch.status,
            started_at=now()
        )
        return batch


class BatchPlansSerializer(BatchSerializer):
    """
    Extended Batch serializer that includes all associated plans.
    Uses individual plan serializers that inherit from PlanResponseMixin.
    """
    plans = serializers.SerializerMethodField()

    class Meta(BatchSerializer.Meta):
        fields = BatchSerializer.Meta.fields + ['plans']

    def get_plans(self, obj):
        """
        Get all plans associated with this batch (Text, Image, Audio).
        Each plan serializer already includes PlanResponseMixin fields.
        """
        # Get all plans using the batch's get_all_plans method
        all_plans = obj.get_all_plans()
        
        # Filter out normal plans if needed (based on your original logic)
        # This assumes there might be a 'normal_plan' field on plans
        filtered_plans = [plan for plan in all_plans if not getattr(plan, 'normal_plan', False)]
        
        plans_data = []
        
        for plan in filtered_plans:
            # Use the appropriate serializer based on plan type
            # All these serializers inherit from PlanResponseMixin
            if plan.__class__.__name__ == 'TextPlan':
                serializer = TextPlanSerializer(plan, context=self.context)
                data = serializer.data
                data['plan_type'] = 'text'
            elif plan.__class__.__name__ == 'ImagePlan':
                serializer = ImagePlanSerializer(plan, context=self.context)
                data = serializer.data
                data['plan_type'] = 'image'
            elif plan.__class__.__name__ == 'AudioPlan':
                serializer = AudioPlanSerializer(plan, context=self.context)
                data = serializer.data
                data['plan_type'] = 'audio'
            else:
                # Fallback for any other plan types
                data = {
                    'id': plan.id,
                    'plan_type': plan.__class__.__name__.lower().replace('plan', ''),
                    'title': getattr(plan, 'name', ''),
                    'description': getattr(plan, 'description', ''),
                    'status': getattr(plan, 'status', ''),
                }
            
            plans_data.append(data)
        
        return plans_data
