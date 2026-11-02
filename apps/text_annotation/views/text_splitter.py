from apps.project_management.models.text_plan import TextSplitter
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

# from apps.text_annotation.models.plan_text_segmentation import TextSplitter
from apps.text_annotation.serializers.text_splitter import TextSplitterSerializer


class TextSplitterView(generics.ListCreateAPIView):
    serializer_class = TextSplitterSerializer
    permission_classes = [IsAuthenticated]
    query_set = TextSplitter.objects.all()
