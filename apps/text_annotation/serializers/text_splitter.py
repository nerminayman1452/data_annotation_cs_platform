from apps.project_management.models.text_plan import TextSplitter
from rest_framework import serializers

# from apps.text_annotation.models.plan_text_segmentation import TextSplitter


class TextSplitterSerializer(serializers.ModelSerializer):
    class Meta:
        model = TextSplitter
        fields = "__all__"
