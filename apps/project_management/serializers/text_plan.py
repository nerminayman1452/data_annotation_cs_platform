import os
from apps.project_management.models.batch import Batch
from apps.project_management.serializers.plan import PlanResponseMixin, UnifiedLabelMixin
from rest_framework import serializers
from django.db import transaction
from django.contrib.auth.models import User

from apps.project_management.models.text_plan import (
    TextPlan, TextPlanConfig, TextPlanCostConfig, TextPlanEstimationConfig,
    TextPlanRawData, TextLabelType, TextErrorType, TextSentenceType, TextValidationType, TextSplitter, TextPlanStatusHistory
)
from apps.planning.models.measure_unit import MeasureUnits


# --- Simple Serializers for Metadata Views ---
class TextLabelTypeSerializer(serializers.ModelSerializer):
    class Meta: model = TextLabelType; fields = '__all__'

class TextErrorTypeSerializer(serializers.ModelSerializer):
    class Meta: model = TextErrorType; fields = '__all__'

class TextSentenceTypeSerializer(serializers.ModelSerializer):
    class Meta: model = TextSentenceType; fields = '__all__'

class TextValidationTypeSerializer(serializers.ModelSerializer):
    class Meta: model = TextValidationType; fields = '__all__'

# --- 1. Helper Mixin for Dynamic Label Creation ---

# class TextLabelTypesMixin(serializers.Serializer):
#     """
#     Handles mixed input: [1, "New Label"] -> Creates or Retrieves objects
#     """
#     # We map the input 'allowed_labels' to an internal name 'labels_input' 
#     # to avoid conflict with the model field during direct assignment.
#     allowed_labels = serializers.ListField(child=serializers.JSONField(), required=False, source='labels_input')
#     allowed_errors = serializers.ListField(child=serializers.JSONField(), required=False, source='errors_input')
#     allowed_sentence_types = serializers.ListField(child=serializers.JSONField(), required=False, source='sentence_types_input')
#     allowed_validation_types = serializers.ListField(child=serializers.JSONField(), required=False, source='validation_types_input')

#     @staticmethod
#     def process_items(model_class, field_name, items):
#         """Generic processor for (Model, field_name='label_type', input_list)"""
#         results = []
#         if not items:
#             return results

#         for item in items:
#             if isinstance(item, int):
#                 try:
#                     results.append(model_class.objects.get(id=item))
#                 except model_class.DoesNotExist:
#                     raise serializers.ValidationError(f"{model_class._meta.verbose_name} ID {item} does not exist.")
#             elif isinstance(item, str):
#                 kwargs = {field_name: item.strip()}
#                 obj, _ = model_class.objects.get_or_create(**kwargs)
#                 results.append(obj)
#             else:
#                 raise serializers.ValidationError(f"Invalid input: {item}")
#         return results


# --- 2. Config Serializers ---
class TextPlanCostConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = TextPlanCostConfig
        fields = ['cost_per_unit', 'is_approved', 'approved_at']
        read_only_fields = ['approved_at']


class TextPlanEstimationConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = TextPlanEstimationConfig
        fields = ['start_date', 'has_auto_progress', 'total_units', 'duration', 'duration_unit', 'measure_unit']


class TextPlanConfigSerializer(UnifiedLabelMixin, serializers.ModelSerializer):
    segmentation_splitter = serializers.PrimaryKeyRelatedField(
        queryset=TextSplitter.objects.all(), required=False, allow_null=True
    )
    
    class Meta:
        model = TextPlanConfig
        fields = [
            'config', 'workers_per_task', 'task_distribution_mode', 'standard',
            'time_per_task', 'acceptance_agreement',
            'max_summary_length', 'min_summary_length', 'segmentation_splitter',
            # Inherited from Mixin
            # 'labels_input' # Unified Input
            # 'allowed_labels', 'allowed_errors', 'allowed_sentence_types', 'allowed_validation_types'
        ]

    # def to_representation(self, instance):
    #     ret = super().to_representation(instance)
    #     data = []

    #     def fmt(qs, name_field, key): 
    #         return [{'id': x.id, 'value': getattr(x, name_field), 'type': key} for x in qs]

    #     if instance.allowed_labels.exists():
    #         data.extend(fmt(instance.allowed_labels.all(), 'label_type', 'LABEL'))
    #     if instance.allowed_errors.exists():
    #         data.extend(fmt(instance.allowed_errors.all(), 'error_type', 'ERROR'))
    #     if instance.allowed_sentence_types.exists():
    #         data.extend(fmt(instance.allowed_sentence_types.all(), 'sentence_type', 'SENTENCE'))
    #     if instance.allowed_validation_types.exists():
    #         data.extend(fmt(instance.allowed_validation_types.all(), 'validation_type', 'VALIDATION'))
            
    #     ret['labels_output'] = data
    #     return ret

    @staticmethod
    def save_m2m_relations(config_instance, validated_data):
        labels_data = validated_data.pop('labels_input', None)
        if not labels_data:
            return

        plan = config_instance.plan
        
        # 1. Determine Default Type based on Plan Type
        default_key = 'VALIDATION' if plan.annotation_type == 'VALIDATION' else 'LABEL'

        # 2. Define Full Mapping
        type_map = {
            'LABEL':      (TextLabelType, 'label_type'),
            'ERROR':      (TextErrorType, 'error_type'),
            'SENTENCE':   (TextSentenceType, 'sentence_type'),
            'VALIDATION': (TextValidationType, 'validation_type')
        }

        # 3. Process
        buckets = UnifiedLabelMixin.resolve_labels(labels_data, type_map, default_key)

        # 4. Save (Order doesn't matter)
        if buckets['LABEL']:      config_instance.allowed_labels.set(buckets['LABEL'])
        if buckets['ERROR']:      config_instance.allowed_errors.set(buckets['ERROR'])
        if buckets['SENTENCE']:   config_instance.allowed_sentence_types.set(buckets['SENTENCE'])
        if buckets['VALIDATION']: config_instance.allowed_validation_types.set(buckets['VALIDATION'])


# --- 3. Main Plan Serializer ---

class TextPlanSerializer(PlanResponseMixin, serializers.ModelSerializer):
    # plan_config = TextPlanConfigSerializer(source='config', required=False)
    # cost_config = TextPlanCostConfigSerializer(required=False)
    # estimation_config = TextPlanEstimationConfigSerializer(required=False)

    # Cost Config
    cost_per_unit = serializers.DecimalField(
        required=False, 
        source='cost_config.cost_per_unit', 
        max_digits=10, 
        decimal_places=3)
    is_approved = serializers.BooleanField(required=False, source='cost_config.is_approved')
    
    # Estimation Config
    start_date = serializers.DateField(required=False, source='estimation_config.start_date')
    has_auto_progress = serializers.BooleanField(required=False, source='estimation_config.has_auto_progress')
    # total_units, duration, etc. are usually calculated, but if input is needed:
    duration = serializers.IntegerField(required=False, source='estimation_config.duration')
    duration_unit = serializers.CharField(required=False, source='estimation_config.duration_unit')
    total_units = serializers.IntegerField(required=False, source='estimation_config.total_units')
    measure_unit = serializers.PrimaryKeyRelatedField(
        queryset=MeasureUnits.objects.all(),
        required=False,
        source='estimation_config.measure_unit',
        allow_null=True
    )
    # Plan Config
    config = serializers.JSONField(required=False, source='config.config')
    workers_per_task = serializers.IntegerField(required=False, source='config.workers_per_task')
    task_distribution_mode = serializers.CharField(required=False, source='config.task_distribution_mode')
    standard = serializers.FloatField(required=False, source='config.standard')
    time_per_task = serializers.IntegerField(required=False, source='config.time_per_task')
    acceptance_agreement = serializers.IntegerField(required=False, source='config.acceptance_agreement')
    max_summary_length = serializers.IntegerField(required=False, source='config.max_summary_length')
    min_summary_length = serializers.IntegerField(required=False, source='config.min_summary_length')
    
    segmentation_splitter = serializers.PrimaryKeyRelatedField(
        queryset=TextSplitter.objects.all(), required=False, allow_null=True, source='config.segmentation_splitter'
    )
    
    # # Unified Labels Input (Not a model field, purely Write Only)
    # labels_input = serializers.ListField(
    #     child=serializers.JSONField(), required=False, write_only=True
    # )

    
    batch = serializers.PrimaryKeyRelatedField(
        queryset=Batch.objects.all(), required=False, allow_null=True, write_only=True
    )

    class Meta:
        model = TextPlan
        fields = [
            # Main Fields
            'id', 'title', 'description', 'name', 'annotation_type', 'is_locked', 'batch',
            'created_by', 'status', 'created_at', 'updated_at',
            
            # Flattened Config Fields
            'cost_per_unit','is_approved',
            'start_date', 'duration', 'duration_unit', 'measure_unit','total_units',
            'config', 'workers_per_task', 'task_distribution_mode', 'standard', 'time_per_task',
            'acceptance_agreement', 'max_summary_length', 'min_summary_length', 'segmentation_splitter',
            # 'labels_input', # Write only

            # Calculated/Read-Only Mixin Fields
            'batch_name', 'project_title', 'organization_title', 'batch_id', 
            'rates', 'efforts', 'task_cost', 'platform_fee', 'total_estimated_budget', 
            'end_date', 'actual_end_date', 'duration_days', 'duration_weeks',
            'actual_units', 'progress', 'progress_till_now', 'weight', 'weight_times_progress',
            'quality', 'workers', 'has_auto_progress', 'is_actual', 'actual_plan_detail',
        ]
        read_only_fields = ['status', 'created_at', 'updated_at','is_approved']

    def validate(self, attrs):
        batch = attrs.get('batch')
        if batch:
            is_owner = Batch.objects.filter(id=batch.id, created_by=int(self.context['request'].user.id)).exists()
            if not is_owner:
                raise serializers.ValidationError("You do not have permission to add plans to this batch.")
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        # 1. Separate Data Streams using the keys defined in `source` or field name
        
        # Helper to safely pop nested source fields that DRF places in validated_data
        # Note: DRF 3.x with source='config.field' might pass data nested or flat depending on version.
        # We assume standard behavior where writable nested source isn't auto-merged, so we access keys directly.
        # If DRF merges them into 'config': {}, we handle that.
        
        cost_data = {}
        est_data = {}
        config_data = {}
        
        # Extract Nested Dictionaries if DRF grouped them (common in newer DRF with source)
        raw_config = validated_data.pop('config', {})
        raw_cost = validated_data.pop('cost_config', {})
        raw_est = validated_data.pop('estimation_config', {})

        # Merge any fields that didn't get grouped (if any) or flatten structure logic
        # For simplicity in this implementation, we map manually to ensure control
        
        # Cost
        if 'cost_per_unit' in raw_cost: cost_data['cost_per_unit'] = raw_cost['cost_per_unit']
        
        # Estimation
        for k in ['start_date', 'has_auto_progress', 'duration', 'duration_unit', 'total_units']:
             if k in raw_est: est_data[k] = raw_est[k]

        if 'measure_unit' in raw_est: 
            est_data['measure_unit_id'] = raw_est['measure_unit'].id if raw_est['measure_unit'] else None

        # Config
        for k in ['workers_per_task', 'task_distribution_mode', 'standard', 'time_per_task', 
                  'acceptance_agreement', 'max_summary_length', 'min_summary_length', 'segmentation_splitter']:
             if k in raw_config: config_data[k] = raw_config[k]
        
        # Handle 'config' JSON field specifically (name collision with relation name)
        if 'config' in raw_config: config_data['config'] = raw_config['config']

        # Labels (Direct field)
        labels_input = validated_data.pop('labels_input', None)

        # 2. Get User
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            validated_data['created_by'] = int(request.user.id)

        # 3. Create Plan (validated_data now only contains Plan fields)
        plan = TextPlan.objects.create(**validated_data)

        # 4. Create Related Configs
        TextPlanCostConfig.objects.create(plan=plan, **cost_data)
        TextPlanEstimationConfig.objects.create(plan=plan, **est_data)
        
        config_instance = TextPlanConfig.objects.create(plan=plan, **config_data)

        # 5. Handle M2M Logic
        # TextPlanConfigLogic.save_m2m_relations(config_instance, labels_input)

        return plan

    @transaction.atomic
    def update(self, instance, validated_data):
        # 1. Pop nested dictionaries created by source='related.field'
        cost_data = validated_data.pop('cost_config', {})
        est_data = validated_data.pop('estimation_config', {})
        config_data = validated_data.pop('config', {})  # Refers to TextPlanConfig, not the JSON field 'config' inside it

        # 2. Update the main plan instance (flat fields)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # 3. Update related Cost Config
        if cost_data and hasattr(instance, 'cost_config'):
            cost_config = instance.cost_config
            for attr, value in cost_data.items():
                setattr(cost_config, attr, value)
            cost_config.save()
        
        # 4. Update related Estimation Config
        if est_data and hasattr(instance, 'estimation_config'):
            estimation_config = instance.estimation_config
            for attr, value in est_data.items():
                # This handles 'measure_unit' automatically (assigning the object directly)
                setattr(estimation_config, attr, value)
            estimation_config.save()
        
        # 5. Update related Plan Config
        if config_data and hasattr(instance, 'config'):
            plan_config = instance.config
            for attr, value in config_data.items():
                # This handles 'segmentation_splitter' automatically (assigning the object directly)
                setattr(plan_config, attr, value)
            plan_config.save()
        
        return instance

# --- 4. Raw Data Serializer (Multiple Files) ---

class TextPlanRawDataSerializer(serializers.ModelSerializer):
    # Explicitly define 'file' as a ListField for multiple uploads
    file = serializers.ListField(
        child=serializers.FileField(),
        write_only=True,
        help_text="Upload one or multiple text files (.txt, .csv, .json, .tsv, .xml)"
    )

    file_size = serializers.SerializerMethodField(read_only=True)
    file_type = serializers.SerializerMethodField(read_only=True)
    file_name = serializers.CharField(read_only=True)
    plan = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = TextPlanRawData
        fields = [
            'id', 'file', 'plan', 'file_name', 'file_size', 'file_type', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def get_file_size(self, obj):
        try:
            if obj.file:
                return f"{obj.file.size / 1024:.2f} KB"
        except Exception:
            return "0 KB"
        return "0 KB"

    def get_file_type(self, obj):
        if obj.file_name:
            _, ext = os.path.splitext(obj.file_name)
            return ext.lower()
        return ""

    def validate_file(self, value):
        """
        Validates a LIST of files for Text Batches.
        """
        limit_mb = 50 # Text files can be large, but usually smaller than images. 50MB is generous.
        valid_extensions = ['.txt', '.csv', '.json', '.xml', '.tsv', '.md','.xlsx']

        for single_file in value:
            # Size Check
            if single_file.size > limit_mb * 1024 * 1024:
                raise serializers.ValidationError(f"File '{single_file.name}' is too large. Limit is {limit_mb}MB")
            
            # Extension Check
            ext = os.path.splitext(single_file.name)[1].lower()
            if ext not in valid_extensions:
                raise serializers.ValidationError(f"File '{single_file.name}' has unsupported extension: {ext}")

        return value

    def create(self, validated_data):
        plan = validated_data.get('plan')
        files = validated_data.get('file') # This is a list
        
        created_instances = []
        for f in files:
            instance = TextPlanRawData.objects.create(
                plan=plan, 
                file=f,
                file_name=f.name
            )
            created_instances.append(instance)
        
        return created_instances[0]

class TextPlanStatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TextPlanStatusHistory
        fields = ['id', 'plan', 'status', 'started_at', 'ended_at', ]

class TextPlanRawDataQualitySerializer(serializers.ModelSerializer):

    class Meta:
        model = TextPlanRawData
        fields = ['id', 'quality', 'file']
        read_only_fields = ['file']


    