from rest_framework.generics import ListCreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError

from apps.text_annotation.services.segmentation_process import SegmentationProcessor
from apps.text_annotation.models.task_text_segmentation import TextSegmentationTaskResult
from apps.text_annotation.serializers.task_text_segmentation import TextSegmentationTaskResultSerializer


class TextSegmentationTasksAPIView(ListCreateAPIView):
    serializer_class = TextSegmentationTaskResultSerializer
    permission_classes = [IsAuthenticated]
    queryset = TextSegmentationTaskResult.objects.all()

    def post(self, request, *args, **kwargs):
        plan_id = kwargs.get('plan_id')
        batch_id = kwargs.get('batch_id')
        if not plan_id or not batch_id:
            return Response({"detail": "batch_id and plan_id are required in the URL."},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            processor = SegmentationProcessor(plan_id, batch_id)
            created_tasks = processor.process_batch_segmented_data_list()
            serializer = self.get_serializer(created_tasks, many=True)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response({'errors': e.detail}, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        plan_id = kwargs.get('plan_id')
        batch_id = kwargs.get('batch_id')

        if not plan_id or not batch_id:
            return Response({"detail": "batch_id and plan_id are required in the URL."},
                            status=status.HTTP_400_BAD_REQUEST)

        queryset = self.get_queryset().filter(
            plan_segmentation_id=plan_id,
            batch_data__batch_id=batch_id
        )

        if not queryset.exists():
            return Response(
                {"message": "There are no segmentation tasks generated yet!"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
