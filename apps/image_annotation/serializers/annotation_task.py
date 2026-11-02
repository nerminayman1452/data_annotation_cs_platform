from rest_framework import serializers

from apps.image_annotation.models.task_annotation import ImageTaskAnnotation
from apps.image_annotation.serializers.annotation_submission import ImageAnnotationSubmissionSerializer


class ImageAnnotationTaskSerializer(serializers.ModelSerializer):
    """
    Assignment View: Shows which item is assigned and the worker's progress.
    """
    # Use the serializer above to show the current submission
    submission = serializers.SerializerMethodField()

    # Basic details about the item being annotated
    image_url = serializers.SerializerMethodField()
    batch_name = serializers.CharField(source="batch_file.batch.batch_name", read_only=True)

    class Meta:
        model = ImageTaskAnnotation
        fields = [
            "id",
            "plan_task",  # ID of the task
            "batch_name",
            "image_url",
            "submission",  # The nested result
            "created_at",
        ]

    def get_submission(self, obj):
        # Helper to get the latest submission using the property from your Abstract Model
        sub = obj.last_submission
        if sub:
            return ImageAnnotationSubmissionSerializer(sub).data
        return None

    def get_image_url(self, obj):
        request = self.context.get("request")
        # Navigate: Assignment -> BatchTask -> RawData -> File
        raw_data = obj.plan_task.plan_file
        if raw_data and raw_data.file:
            url = raw_data.file.url
            return request.build_absolute_uri(url) if request else url
        return None