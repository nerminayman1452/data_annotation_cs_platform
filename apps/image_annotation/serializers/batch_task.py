from apps.image_annotation.models.plan_task import ImagePlanTask
from rest_framework import serializers

from apps.image_annotation.serializers.annotation_task import ImageAnnotationTaskSerializer


class ImageBatchTaskSerializer(serializers.ModelSerializer):
    """
    Manager View: Shows the image and ALL worker submissions.
    """
    image_url = serializers.SerializerMethodField()

    # 1. List of all assignments/submissions for this image
    annotations = ImageAnnotationTaskSerializer(source="assignments", many=True, read_only=True)

    # 2. Progress Stats
    progress = serializers.SerializerMethodField()

    class Meta:
        model = ImagePlanTask
        fields = [
            "id",
            "plan",
            "image_url",
            "accepted_by",  # Status (PENDING, IAA, etc)
            "finalized_data",  # The Consensus Result
            "annotations",  # List of worker results
            "progress",  # Stats
            "created_at",
        ]
        read_only_fields = ['accepted_by', 'finalized_data', 'created_at', 'progress', 'annotations']

    def get_image_url(self, obj):
        request = self.context.get("request")
        if obj.plan_file and obj.plan_file.file:
            url = obj.plan_file.file.url
            return request.build_absolute_uri(url) if request else url
        return None

    def get_progress(self, obj):
        """
        Replaces your old 'progress_for_annotator' logic but scopes it
        to this specific task item.
        """
        total_assignments = obj.assignments.count()
        completed = obj.assignments.filter(
            submissions__status__in=["SUBMITTED", "ACCEPTED"]
        ).distinct().count()

        return {
            "total_assigned": total_assignments,
            "completed": completed,
            "is_finished": obj.is_complete  # Uses the property from your Abstract Model
        }