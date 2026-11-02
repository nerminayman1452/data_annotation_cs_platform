from rest_framework import serializers

from apps.project_management.models.plan_members import PlanMember
from apps.text_annotation.models.review_text_labelling import ReviewTextLabellingResult
from apps.text_annotation.models.task_text_labelling import TextLabellingTaskResult


class ReviewTextLabellingResultSerializer(serializers.ModelSerializer):
    task = serializers.PrimaryKeyRelatedField(queryset=TextLabellingTaskResult.objects.all())

    class Meta:
        model = ReviewTextLabellingResult
        fields = [
            'id',
            'reviewer',
            'task',
            'feedback',
            'role',
            'is_accepted',
            'status',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, attrs):
        task = attrs.get('task')
        batch = task.plan
        reviewer = PlanMember.objects.filter(batch=batch.id, user_role='Reviewer').exists()
        if task.status != 'submitted':
            raise serializers.ValidationError({"task": "Task must be submitted before review."})
        if not reviewer:
            raise serializers.ValidationError("No reviewers assigned to this batch.")
