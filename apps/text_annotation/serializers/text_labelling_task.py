from rest_framework import serializers

from apps.project_management.models import  PlanMember
from apps.project_management.models.batch import Batch
from apps.project_management.models.text_plan import TextPlanRawData
# from apps.project_management.models.batch_data import BatchData
# from apps.project_management.models.segmented_batch_data import SegmentedBatchData
# from apps.text_annotation.models.plan_text_labelling import TextLabellingPlan
from apps.text_annotation.models.task_text_labelling import TextLabellingTaskResult


class GenerateTextLabellingTaskSerializer(serializers.ModelSerializer):
    batch = serializers.PrimaryKeyRelatedField(queryset=Batch.objects.all())
    # plan = serializers.PrimaryKeyRelatedField(queryset=TextLabellingPlan.objects.all())

    def validate(self, attrs):
        batch = attrs.get('batch')
        plan = attrs.get('plan')
        annotator = PlanMember.objects.filter(batch=batch, user_role='Annotator').exists()
        batch_data= TextPlanRawData.objects.filter(batch_id=batch.id).exists()

        if not batch:
            raise serializers.ValidationError("Batch is required.")

        if not plan:
            raise serializers.ValidationError("Text Labelling plan is required.")

        if batch.created_by != self.context['request'].user.id:
            raise serializers.ValidationError("You do not have permission to generate tasks to this batch.")

        # if not TextLabellingPlan.objects.filter(id=plan.id).exists():
        #     raise serializers.ValidationError("Text Labelling Plan with this ID does not exist.")

        if not batch_data:
            raise serializers.ValidationError("No batch data found for the selected batch.")

        if not annotator:
            raise serializers.ValidationError("No annotators assigned to this batch.")

        # if plan.content_type in ["Paragraph", "Sentence"]:
        #     segmented_data = SegmentedBatchData.objects.filter(batch_data=batch_data.id).first()

            # if not segmented_data :
            #     raise serializers.ValidationError("There's no segmented data yet.")

            # if not segmented_data.paragraphs and not segmented_data.sentences:
            #     raise serializers.ValidationError("There's no paragraphs or sentences yet in the segmented data.")

        return attrs

    class Meta:
        model = TextLabellingTaskResult
        fields = ['id', 'annotator', 'batch_data','batch','data_content', 'plan', 'status', 'created_at',"label_type_result","error_type_result","sentence_type_result"]
        read_only_fields = ['annotator','status','created_at']