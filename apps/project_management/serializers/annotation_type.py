from rest_framework import serializers

from apps.project_management.models.annotation_type import AnnotationType


class AnnotationTypeSerializer(serializers.ModelSerializer):
    # Optional: Display readable label for media type (e.g. "Text" instead of "TEXT")
    plan_type = serializers.CharField(write_only=True)

    class Meta:
        model = AnnotationType
        fields = ['id', 'name', 'plan_type', 'url', 'comparison_key',]
