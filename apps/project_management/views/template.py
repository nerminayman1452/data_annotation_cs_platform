from apps.project_management.serializers.template import BatchTemplateSerializer, ImagePlanReuseSerializer, TextPlanReuseSerializer
from rest_framework import generics, permissions
from apps.project_management.models.batch import Batch
from drf_spectacular.utils import extend_schema


#-------Batch Template Views-------
@extend_schema(
    tags=['Batches'],
    description='Create a new batch from a template',
    responses={
        201: BatchTemplateSerializer()
    }
)
class BatchCreateFromTemplateView(generics.CreateAPIView):
    """
    POST: Creates a new Batch (and child plans) based on a Template Batch ID.
    """
    queryset = Batch.objects.all()
    serializer_class = BatchTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]


@extend_schema(
    tags=['Batches'],
    description='List all batch templates',
    responses={
        200: BatchTemplateSerializer(many=True)
    }
)
class BatchTemplateListView(generics.ListAPIView):
    """
    GET: List all batch templates
    """
    queryset = Batch.objects.filter(is_template=True)
    serializer_class = BatchTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]




#-------Text Plan Template Views-------
@extend_schema(
    tags=['Text Plans'],
    description='Create a new text plan from existing plans',
    responses={
        201: TextPlanReuseSerializer()
    }
)
class TextPlanCreateReuseView(generics.CreateAPIView):
    """
    POST: Creates a new Text Plan reusing Config/Data/Results from existing plans.
    """
    serializer_class = TextPlanReuseSerializer
    permission_classes = [permissions.IsAuthenticated]

#-------Image Plan Template Views-------
@extend_schema(
    tags=['Image Plans'],
    description='Create a new image plan from existing plans',
    responses={
        201: ImagePlanReuseSerializer()
    }
)
class ImagePlanCreateReuseView(generics.CreateAPIView):
    """
    POST: Creates a new Image Plan reusing Config/Data/Results from existing plans.
    """
    serializer_class = ImagePlanReuseSerializer
    permission_classes = [permissions.IsAuthenticated]


#-------Audio Plan Template Views-------
# class AudioPlanCreateReuseView(generics.CreateAPIView):
#     """
#     POST: Creates a new audio Plan reusing Config/Data/Results from existing plans.
#     """
#     serializer_class = AudioPlanReuseSerializer
#     permission_classes = [permissions.IsAuthenticated]