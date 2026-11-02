import os

from django.db import transaction
from rest_framework import serializers

from apps.planning.models.measure_unit import MeasureUnits

from apps.project_management.models.batch import Batch
from apps.project_management.models.image_plan import DetectionLabelType, ImagePlan, ImagePlanConfig, ImagePlanCostConfig, \
    ImagePlanEstimationConfig, ImageLabelType, ImagePlanStatusHistory, PolygonLabelType
from apps.project_management.models.image_plan import ImagePlanRawData
from apps.project_management.serializers.plan import PlanResponseMixin, UnifiedLabelMixin


# --- Simple Serializers for Metadata Views ---
class ImageLabelTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImageLabelType
        fields = '__all__'

class DetectionLabelTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetectionLabelType
        fields = '__all__'

class PolygonLabelTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PolygonLabelType
        fields = '__all__'

# class LabelTypesMixin(serializers.Serializer):
#     """
#     Handles mixed input: [1, "New Label"] -> Creates or Retrieves objects for different label types
#     """
#     classification_labels = serializers.ListField(child=serializers.JSONField(), required=False, source='classification_labels_input')
#     detection_labels = serializers.ListField(child=serializers.JSONField(), required=False, source='detection_labels_input')
#     polygon_labels = serializers.ListField(child=serializers.JSONField(), required=False, source='polygon_labels_input')

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


class ImagePlanCostConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImagePlanCostConfig
        fields = ['cost_per_unit', 'is_approved', 'approved_at']
        read_only_fields = ['approved_at']


class ImagePlanEstimationConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImagePlanEstimationConfig
        fields = ['start_date', 'has_auto_progress', 'total_units', 'duration', 'duration_unit', 'measure_unit']


class ImagePlanConfigSerializer(UnifiedLabelMixin, serializers.ModelSerializer):
    class Meta:
        model = ImagePlanConfig
        fields = [
            'config', 'workers_per_task', 'task_distribution_mode', 'standard',
            'time_per_task', 'acceptance_agreement',
            # Inherited from Mixin
            # 'labels_input'
            # 'classification_labels', 'detection_labels', 'polygon_labels'
        ]

    # def to_representation(self, instance):
    #     ret = super().to_representation(instance)
    #     data = []
        
    #     # Helper to format output consistently
    #     def fmt(qs, key): 
    #         return [{'id': x.id, 'value': x.label_type, 'type': key} for x in qs]

    #     if instance.classification_labels.exists():
    #         data.extend(fmt(instance.classification_labels.all(), 'CLASSIFICATION'))
    #     if instance.detection_labels.exists():
    #         data.extend(fmt(instance.detection_labels.all(), 'DETECTION'))
    #     if instance.polygon_labels.exists():
    #         data.extend(fmt(instance.polygon_labels.all(), 'POLYGON'))
        
    #     ret['labels_output'] = data
    #     return ret

    @staticmethod
    def save_m2m_relations(config_instance, validated_data):
        labels_data = validated_data.pop('labels_input', None)
        if not labels_data:
            return

        # 1. Get the raw annotation type from the plan
        plan = config_instance.plan
        raw_type = str(plan.annotation_type).upper()  # Convert to uppercase string (e.g. "IMAGE - CLASSIFIICATION")

        # 2. Normalize to a standard key using Keyword Matching
        #    This fixes the error by finding "CLASSIF" inside "IMAGE - CLASSIFIICATION"
        standard_key = ""
        type_map = {}

        if "CLASSIF" in raw_type:
            standard_key = "CLASSIFICATION"
            type_map = { "CLASSIFICATION": (ImageLabelType, 'label_type') }
            
        elif "DETECT" in raw_type:
            standard_key = "DETECTION"
            type_map = { "DETECTION": (DetectionLabelType, 'label_type') }
            
        elif "POLYGON" in raw_type:
            standard_key = "POLYGON"
            type_map = { "POLYGON": (PolygonLabelType, 'label_type') }
            
        else:
            # Fallback: If absolutely nothing matches
            raise serializers.ValidationError(f"Unknown Annotation Type: {plan.annotation_type}")

        # 3. Process the labels
        try:
            # We assume the default key matches the plan type (e.g. Strings go to CLASSIFICATION if plan is CLASSIFICATION)
            buckets = UnifiedLabelMixin.resolve_labels(labels_data, type_map, standard_key)
        except serializers.ValidationError as e:
            raise serializers.ValidationError(f"Invalid labels for {standard_key} plan. {e.detail[0]}")

        # 4. Save to the correct field
        if standard_key == "CLASSIFICATION" and buckets["CLASSIFICATION"]:
            config_instance.classification_labels.set(buckets["CLASSIFICATION"])
        elif standard_key == "DETECTION" and buckets["DETECTION"]:
            config_instance.detection_labels.set(buckets["DETECTION"])
        elif standard_key == "POLYGON" and buckets["POLYGON"]:
            config_instance.polygon_labels.set(buckets["POLYGON"])

            
class ImagePlanSerializer(PlanResponseMixin, serializers.ModelSerializer):
    # plan_config = ImagePlanConfigSerializer( source='config', required=False)
    # cost_config = ImagePlanCostConfigSerializer(required=False)
    # estimation_config = ImagePlanEstimationConfigSerializer(required=False)

    # Cost
    cost_per_unit = serializers.DecimalField(required=False, source='cost_config.cost_per_unit', max_digits=10, decimal_places=3)
    is_approved = serializers.BooleanField(required=False, source='cost_config.is_approved')

    
    # Estimation
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

    # Config
    config = serializers.JSONField(required=False, source='config.config')
    workers_per_task = serializers.IntegerField(required=False, source='config.workers_per_task')
    task_distribution_mode = serializers.CharField(required=False, source='config.task_distribution_mode')
    standard = serializers.FloatField(required=False, source='config.standard')
    time_per_task = serializers.IntegerField(required=False, source='config.time_per_task')
    acceptance_agreement = serializers.IntegerField(required=False, source='config.acceptance_agreement')
    
    # Labels
    # labels_input = serializers.ListField(child=serializers.JSONField(), required=False, write_only=True)

    batch = serializers.PrimaryKeyRelatedField(
        queryset=Batch.objects.all(),
        required=False,
        allow_null=True,
        write_only=True  # We output flat 'batch_id' from mixin
    )

    class Meta:
        model = ImagePlan
        # We include ALL fields: The Mixin's read-only fields + The Write-only inputs
        fields = [
            'id', 'name', 'annotation_type', 'is_locked', 'batch', 'title', 'description', 
            'created_by', 'status', 'created_at', 'updated_at',
            
            # Flat Configs
            'cost_per_unit','is_approved',
            'start_date','duration', 'duration_unit', 'measure_unit','total_units',
            'config', 'workers_per_task', 'task_distribution_mode', 'standard', 'time_per_task', 'acceptance_agreement',
            # 'labels_input',

            # Mixin Reads
            'batch_name', 'project_title', 'organization_title', 'batch_id', 'rates', 'efforts', 
            'task_cost', 'platform_fee','total_estimated_budget',
            'end_date', 'actual_end_date', 'duration_days', 'duration_weeks',
            'actual_units', 'progress', 'progress_till_now', 'weight', 'weight_times_progress','quality', 
            'workers', 'has_auto_progress', 'is_actual', 'actual_plan_detail',
        ]
        read_only_fields = ['status', 'created_at', 'updated_at','is_approved']

    def validate(self, attrs):
        batch = attrs.get('batch')
        if batch:
            is_owner = Batch.objects.filter(id=batch.id, created_by=int(self.context['request'].user.id)).exists()
            if not is_owner:
                raise serializers.ValidationError("You do not have permission to add plans to this batch.")

        # Add any cross-model validation here
        # e.g., if annotation_type is POLYGONS, ensure annotator_reward > 0.5
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        # 1. Extraction
        cost_data = {}
        est_data = {}
        config_data = {}
        
        raw_config = validated_data.pop('config', {})
        raw_cost = validated_data.pop('cost_config', {})
        raw_est = validated_data.pop('estimation_config', {})

        if 'cost_per_unit' in raw_cost: cost_data['cost_per_unit'] = raw_cost['cost_per_unit']
        
        for k in ['start_date', 'has_auto_progress', 'duration', 'duration_unit', 'total_units']:
             if k in raw_est: est_data[k] = raw_est[k]

        if 'measure_unit' in raw_est: 
            est_data['measure_unit_id'] = raw_est['measure_unit'].id if raw_est['measure_unit'] else None

        for k in ['workers_per_task', 'task_distribution_mode', 'standard', 'time_per_task', 'acceptance_agreement']:
             if k in raw_config: config_data[k] = raw_config[k]
        
        if 'config' in raw_config: config_data['config'] = raw_config['config']
        
        labels_input = validated_data.pop('labels_input', None)

        # 2. User
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            validated_data['created_by'] = int(request.user.id)

        # 3. Create
        plan = ImagePlan.objects.create(**validated_data)
        ImagePlanCostConfig.objects.create(plan=plan, **cost_data)
        ImagePlanEstimationConfig.objects.create(plan=plan, **est_data)
        
        config_instance = ImagePlanConfig.objects.create(plan=plan, **config_data)
        # ImagePlanConfigLogic.save_m2m_relations(config_instance, labels_input)

        return plan

    @transaction.atomic
    def update(self, instance, validated_data):
        # 1. Pop nested dictionaries created by source='related.field'
        # DRF automatically groups dot-notation sources into nested dicts
        cost_data = validated_data.pop('cost_config', {})
        est_data = validated_data.pop('estimation_config', {})
        config_data = validated_data.pop('config', {}) 

        # 2. Update the main plan instance (remaining flat fields)
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
                setattr(estimation_config, attr, value)
            estimation_config.save()
        
        # 5. Update related Plan Config
        if config_data and hasattr(instance, 'config'):
            plan_config = instance.config
            for attr, value in config_data.items():
                setattr(plan_config, attr, value)
            plan_config.save()
        
        return instance
class ImagePlanRawDataSerializer(serializers.ModelSerializer):
    # Explicitly define the file field as a List for Swagger/Schema generation
    file = serializers.ListField(
        child=serializers.FileField(),
        write_only=True,
        help_text="Upload one or multiple files."
    )

    # Read-only fields for the response
    file_size = serializers.SerializerMethodField(read_only=True)
    file_type = serializers.SerializerMethodField(read_only=True)
    file_name = serializers.CharField(read_only=True)  # Read-only, generated in view
    plan = serializers.PrimaryKeyRelatedField(read_only=True)  # Handled by URL

    class Meta:
        model = ImagePlanRawData
        fields = [
            'id',
            'file',
            'plan',
            'file_name',
            'file_size',
            'file_type',
            'created_at',
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
        Validates the LIST of files.
        """
        limit_mb = 10
        valid_extensions = ['.jpg', '.jpeg', '.png', '.bmp']

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
        files = validated_data.get('file')  # This is a list now

        created_instances = []
        for f in files:
            instance = ImagePlanRawData.objects.create(
                plan=plan,
                file=f,
                file_name=f.name
            )
            created_instances.append(instance)

        return created_instances[0]  # Return the first one or wrapper


class ImagePlanStatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ImagePlanStatusHistory
        fields = ['id', 'plan', 'status', 'started_at', 'ended_at', ]

    
class ImagePlanRawDataQualitySerializer(serializers.ModelSerializer):

    class Meta:
        model = ImagePlanRawData
        fields = ['id', 'quality', 'file']
        read_only_fields = ['file']
