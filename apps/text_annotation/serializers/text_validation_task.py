from rest_framework import serializers

from apps.project_management.models import  PlanMember
from apps.project_management.models.batch import Batch
from apps.project_management.models.text_plan import TextPlanRawData
# from apps.project_management.models.segmented_batch_data import SegmentedBatchData
# from apps.text_annotation.models.plan_text_validation import TextValidationPlan
from apps.text_annotation.models.task_text_validation import TextValidationTaskResult


class GenerateTextValidationTaskSerializer(serializers.ModelSerializer):
    batch = serializers.PrimaryKeyRelatedField(queryset=Batch.objects.all())
    # plan = serializers.PrimaryKeyRelatedField(queryset=TextValidationPlan.objects.all())

    def validate(self, attrs):
        batch = attrs.get('batch')
        plan = attrs.get('plan')

        if not batch:
            raise serializers.ValidationError("Batch is required.")

        if not plan:
            raise serializers.ValidationError("Text validation plan is required.")

        if batch.created_by != self.context['request'].user.id:
            raise serializers.ValidationError("You do not have permission to generate tasks to this batch.")

        # if not TextValidationPlan.objects.filter(id=plan.id).exists():
        #     raise serializers.ValidationError("Text Validation Plan with this ID does not exist.")

        if not PlanMember.objects.filter(batch=batch, user_role='Annotator').exists():
            raise serializers.ValidationError("No annotators assigned to this batch.")

        batch_data = TextPlanRawData.objects.filter(batch=batch, plan_validation=plan).first()
        if not batch_data:
            raise serializers.ValidationError("No batch data found for the selected batch and plan.")

        # if plan.content_type in ["Paragraph", "Sentence"]:
        #     segmented_data = SegmentedBatchData.objects.filter(batch_data=batch_data.id).first()
        #
        #     if not segmented_data :
        #         raise serializers.ValidationError("There's no segmented data yet.")
        #
        #     if not segmented_data.paragraphs and not segmented_data.sentences:
        #         raise serializers.ValidationError("There's no paragraphs or sentences yet in the segmented data.")

        return attrs

    class Meta:
        model = TextValidationTaskResult
        fields = ['id', 'annotator', 'batch_data','data_content','batch', 'plan', 'status', 'created_at',"validate_type_result"]
        read_only_fields = ['annotator','status','created_at']