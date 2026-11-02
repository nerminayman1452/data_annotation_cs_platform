from rest_framework import serializers

from django.contrib.auth import get_user_model


class UnifiedLabelMixin(serializers.Serializer):
    """
    Universal Input Handler for Labels.
    Supports:
    1. [ "Label A", "Label B" ] -> Default Type
    2. [ { "type": "ERROR", "value": "Err1" } ] -> Specific Type
    3. [ { "type": "ERROR", "values": ["Err1", "Err2"] } ] -> Batch Specific Type
    """
    labels_input = serializers.ListField(
        child=serializers.JSONField(), 
        required=False, 
        write_only=True,
        help_text="Mix of IDs, Strings, or Batch Objects {values: [], type: 'ERROR'}"
    )

    @staticmethod
    def resolve_labels(labels_data, type_mapping, default_type_key):
        """
        Sorts mixed input into buckets of Database Objects based on the mapping.
        """
        buckets = {key: [] for key in type_mapping.keys()}
        
        if not labels_data:
            return buckets

        for item in labels_data:
            # 1. Determine Type and List of Values to process
            target_key = default_type_key
            values_to_process = []

            if isinstance(item, dict):
                # Get the type (defaulting if missing)
                target_key = item.get('type', default_type_key)

                # Check if it's a BATCH list ("values") or a SINGLE item ("value")
                if 'values' in item and isinstance(item['values'], list):
                    values_to_process = item['values']
                elif 'value' in item:
                    values_to_process = [item['value']]
                else:
                    raise serializers.ValidationError(f"Label input object missing 'value' or 'values': {item}")
            else:
                # It's a simple string/int -> use default type
                values_to_process = [item]

            # 2. Validate Type Key
            if target_key not in type_mapping:
                valid_keys = ", ".join(type_mapping.keys())
                raise serializers.ValidationError(f"Invalid label type '{target_key}'. Allowed: {valid_keys}")

            # 3. Process the List of Values
            ModelClass, field_name = type_mapping[target_key]

            for val in values_to_process:
                if isinstance(val, int):
                    try:
                        obj = ModelClass.objects.get(id=val)
                        buckets[target_key].append(obj)
                    except ModelClass.DoesNotExist:
                        raise serializers.ValidationError(f"{ModelClass._meta.verbose_name} ID {val} not found.")
                
                elif isinstance(val, str):
                    kwargs = {field_name: val.strip()}
                    obj, _ = ModelClass.objects.get_or_create(**kwargs)
                    buckets[target_key].append(obj)
                
                else:
                    raise serializers.ValidationError(f"Invalid value format in {target_key}: {val}")

        return buckets

class PlanResponseMixin(serializers.Serializer):
    """
    Defines the Read-Only output structure required by the frontend/LabelStudio.
    """
    # ID & User
    id = serializers.IntegerField(read_only=True)
    # created_by = SimpleUserSerializer(read_only=True)
    # Hierarchy Info
    batch_name = serializers.CharField(source='batch.name', read_only=True)
    project_title = serializers.CharField(source='batch.project.project_name', read_only=True, default="N/A")
    organization_title = serializers.CharField(source='batch.project.organization.name', read_only=True, default="N/A")
    batch_id = serializers.PrimaryKeyRelatedField(source='batch', read_only=True)
    
    # Financials & Targets (Source: estimates.* and cost_config.*)
    rates = serializers.DecimalField( max_digits=10, decimal_places=2, read_only=True, allow_null=True)
    efforts = serializers.DecimalField(source='estimation_config.efforts', max_digits=10, decimal_places=2, read_only=True, allow_null=True)
    task_cost = serializers.DecimalField(source='cost_config.total_cost', max_digits=15, decimal_places=3, read_only=True, allow_null=True)
    platform_fee = serializers.DecimalField(source='cost_config.platform_fee', max_digits=15, decimal_places=3, read_only=True, allow_null=True)
    total_estimated_budget = serializers.DecimalField(source='cost_config.total_estimated_budget', max_digits=15, decimal_places=3, read_only=True, allow_null=True)
    total_units = serializers.IntegerField(source='estimation_config.total_units', read_only=True, allow_null=True)
    cost_per_unit = serializers.DecimalField(source='cost_config.cost_per_unit', max_digits=10, decimal_places=3, read_only=True, allow_null=True)
    measure_units = serializers.PrimaryKeyRelatedField(source='estimation_config.measure_unit', read_only=True)

    # Timing (Source: estimates.* and actuals.*)
    start_date = serializers.DateField(source='estimation_config.start_date', read_only=True)
    end_date = serializers.DateField(source='estimation_config.end_date', read_only=True)
    actual_end_date = serializers.DateTimeField(read_only=True)
    duration_days = serializers.IntegerField(source='estimation_config.duration_days', read_only=True)
    duration_weeks = serializers.FloatField(source='estimation_config.duration_weeks', read_only=True)
    # time_elapsed_percentage = serializers.FloatField(source='actuals.time_elapsed_percent', read_only=True)

    actual_units = serializers.IntegerField(source='total_actual_units', read_only=True)
    
    # Progress & Status (Source: actuals.*)
    status = serializers.CharField(read_only=True)
    progress = serializers.FloatField(source='actual_progress', read_only=True)
    progress_till_now = serializers.FloatField( read_only=True)
    quality = serializers.FloatField(source='actual_quality', read_only=True)
    
    # Strategic (Source: Plan Properties)
    weight = serializers.DecimalField( max_digits=5, decimal_places=2, read_only=True, allow_null=True)
    weight_times_progress = serializers.DecimalField(source='weighted_progress', max_digits=5, decimal_places=2, read_only=True, allow_null=True)
    
    # Config/Operational (Source: config.*)
    standard = serializers.IntegerField(source='config.standard', read_only=True)
    workers = serializers.IntegerField(source='total_workforce', read_only=True)
    has_auto_progress = serializers.BooleanField(source='estimation_config.has_auto_progress', read_only=True)
    
    # Meta
    is_actual = serializers.SerializerMethodField()
    actual_plan_detail = serializers.SerializerMethodField()
    title = serializers.CharField(source='name', read_only=True)
    description = serializers.CharField(default="", read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    def get_is_actual(self, obj):
        # Logic: If it has started or has progress, consider it actual
        return obj.status != 'pending'

    def get_actual_plan_detail(self, obj):
        # Return a summary string or JSON dump
        return f"{obj.annotation_type} Plan"