from django.db import transaction
from rest_framework import serializers

# from apps.project_management.helpers.cloning import PlanCloner
from apps.project_management.helpers.plan_cloner import PlanCloner
from apps.project_management.models.batch import Batch
from apps.project_management.models.image_plan import ImagePlan
from apps.project_management.models.text_plan import TextPlan
from apps.project_management.models.audio_plan import AudioPlan


# 1. BATCH TEMPLATE SERIALIZER
class BatchTemplateSerializer(serializers.ModelSerializer):
    """
    Creates a new Batch by cloning an existing 'Template' Batch
    and all its associated Plans + Configs.
    """
    template_batch_id = serializers.PrimaryKeyRelatedField(
        queryset=Batch.objects.filter(is_template=True),
        write_only=True,
        source='template_batch'
    )

    # Optional: Override name/project for the new batch
    name = serializers.CharField(required=False)

    class Meta:
        model = Batch
        fields = ['id', 'template_batch_id', 'name', 'project', 'total_amount', 'is_template', 'is_approved', 'status']
        read_only_fields = ['id', 'is_approved', 'status']

    @transaction.atomic
    def create(self, validated_data):
        template_batch = validated_data.pop('template_batch')

        # 1. Create the New Batch Object
        # We start by copying the template's attributes
        new_batch_data = {
            'name': validated_data.get('name', f"Copy of {template_batch.name}"),
            'project': validated_data.get('project', template_batch.project),
            'total_amount': validated_data.get('total_amount', template_batch.total_amount),
            'is_template': False,  # New batch is usually not a template itself
            'is_approved': False,
            'created_by': self.context['request'].user.id
        }

        new_batch = Batch.objects.create(**new_batch_data)

        # 2. Iterate ALL Plan Types to clone them
        # Register all your plan models here
        plan_models = [TextPlan, ImagePlan]  # Add AudioPlan when ready

        for ModelClass in plan_models:
            # Find all plans of this type in the template batch
            source_plans = ModelClass.objects.filter(batch=template_batch)

            for plan in source_plans:
                PlanCloner.clone_plan(
                    source_plan=plan,
                    target_batch=new_batch,
                    reuse_data=False,  # Templates usually don't carry raw data
                    reuse_results=False
                )

        return new_batch


# 2. PLAN REUSE SERIALIZER

def create_reuse_serializer(MetaModel):
    """
    Factory function to generate ReuseSerializers for different Plan Models.
    """

    class PlanReuseSerializer(serializers.ModelSerializer):
        batch = serializers.PrimaryKeyRelatedField(queryset=Batch.objects.all())

        reuse_config_from = serializers.PrimaryKeyRelatedField(
            queryset=MetaModel.objects.all(), write_only=True, required=False, allow_null=True
        )
        reuse_data_from = serializers.PrimaryKeyRelatedField(
            queryset=MetaModel.objects.all(), write_only=True, required=False, allow_null=True
        )
        reuse_results_from = serializers.PrimaryKeyRelatedField(
            queryset=MetaModel.objects.all(), write_only=True, required=False, allow_null=True
        )

        class Meta:
            model = MetaModel
            fields = ['id', 'name', 'batch', 'reuse_config_from', 'reuse_data_from', 'reuse_results_from']

        def validate(self, attrs):
            batch = attrs.get('batch')
            user = self.context['request'].user
            if batch.created_by != user.id and not user.is_staff:
                raise serializers.ValidationError("Permission denied for this batch.")
            return attrs

        @transaction.atomic
        def create(self, validated_data):
            config_source = validated_data.pop('reuse_config_from', None)
            data_source = validated_data.pop('reuse_data_from', None)
            results_source = validated_data.pop('reuse_results_from', None)

            if not config_source:
                raise serializers.ValidationError("You must provide 'reuse_config_from'.")

            # 1. Clone Config & Base Plan
            new_plan = PlanCloner.clone_plan(
                source_plan=config_source,
                target_batch=validated_data['batch'],
                name_prefix="[Cloned] ",
                reuse_data=False,
                reuse_results=False
            )

            # Update Name
            if 'name' in validated_data:
                new_plan.name = validated_data['name']
                new_plan.save()

            # 2. Reuse Data
            if data_source:
                PlanCloner._clone_raw_data(data_source, new_plan)

            # 3. Reuse Results
            if results_source:
                PlanCloner._clone_results_as_raw_data(results_source, new_plan)

            return new_plan

    return PlanReuseSerializer


# Instantiate specific serializers
TextPlanReuseSerializer = create_reuse_serializer(TextPlan)
ImagePlanReuseSerializer = create_reuse_serializer(ImagePlan)
AudioPlanReuseSerializer = create_reuse_serializer(AudioPlan)
