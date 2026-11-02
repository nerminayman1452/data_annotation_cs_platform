from rest_framework import serializers

from apps.audio_annotation.models.task_audio_labelling import AudioLabellingTaskResult

class SegmentSerializer(serializers.Serializer):
    start_time = serializers.FloatField()
    end_time = serializers.FloatField()
    label = serializers.CharField()

class AudioLabellingTaskResultSerializer(serializers.ModelSerializer):
    result = serializers.ListField(
        child=SegmentSerializer(),
        help_text="List of labeled segments with start_time, end_time, and label"
    )

    class Meta:
        model = AudioLabellingTaskResult
        fields = [
            'id',
            'task_name',
            'annotator',
            'template_task',
            'batch',
            'batch_data',
            'plan',
            'status',
            'result',
            'comments',
            'submitted_at',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def validate_result(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Result must be a list.")
        for segment in value:
            if not all(key in segment for key in ['start_time', 'end_time', 'label']):
                raise serializers.ValidationError("Each segment must contain start_time, end_time, and label.")
        return value