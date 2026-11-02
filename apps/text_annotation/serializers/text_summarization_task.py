from rest_framework import serializers

from apps.project_management.models import  PlanMember
from apps.project_management.models.batch import Batch
from apps.project_management.models.text_plan import TextPlanRawData
# from apps.text_annotation.models.plan_text_summarization import TextSummarizationPlan
# from apps.project_management.models.segmented_batch_data import SegmentedBatchData
from apps.text_annotation.models.task_text_summarization import TextSummarizationTaskResult


class GenerateTextSummarizationTaskSerializer(serializers.ModelSerializer):
    batch = serializers.PrimaryKeyRelatedField(queryset=Batch.objects.all())
    # plan = serializers.PrimaryKeyRelatedField(queryset=TextSummarizationPlan.objects.all())

    def validate(self, attrs):
        batch = attrs.get('batch')
        plan = attrs.get('plan')

        if not batch:
            raise serializers.ValidationError("Batch is required.")

        if not plan:
            raise serializers.ValidationError("Text Summarization plan is required.")

        if batch.created_by != self.context['request'].user.id:
            raise serializers.ValidationError("You do not have permission to generate tasks to this batch.")

        # if not TextSummarizationPlan.objects.filter(id=plan.id).exists():
        #     raise serializers.ValidationError("Text Summarization Plan with this ID does not exist.")

        if not PlanMember.objects.filter(batch=batch, user_role='Annotator').exists():
            raise serializers.ValidationError("No annotators assigned to this batch.")

        batch_data= TextPlanRawData.objects.filter(batch_id=batch.id, plan_summarization=plan).exists()
        if not batch_data:
            raise serializers.ValidationError("No batch data found for the selected batch.")

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
        model = TextSummarizationTaskResult
        fields = ['id', 'annotator', 'batch_data','batch','data_content', 'plan', 'status', 'created_at','summarization_result']
        read_only_fields = ['annotator','status','created_at']