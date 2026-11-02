from apps.project_management.views.plan import BaseLabelTypeView, BasePlanDetailsView, BasePlanListCreateView
from drf_spectacular.utils import extend_schema

# from apps.image_annotation.serializers.batch import ImageLabelTypeSerializer
from apps.project_management.models.image_plan import ImagePlan, ImagePlanRawData, ImageLabelType, DetectionLabelType, PolygonLabelType
from apps.project_management.serializers.image_plan import ImagePlanRawDataSerializer, ImagePlanSerializer, ImageLabelTypeSerializer, DetectionLabelTypeSerializer, PolygonLabelTypeSerializer, ImagePlanRawDataQualitySerializer
from apps.project_management.views.plan_data import BasePlanRawDataListCreateView, BasePlanRawDataQualityUpdateView


@extend_schema(
    tags=['Image Plans'],
    description='List all image label types or create a new image label type',
    responses={
        200: ImageLabelTypeSerializer(many=True),
        201: ImageLabelTypeSerializer()
    }
)
class ImageLabelTypeView(BaseLabelTypeView):
    queryset = ImageLabelType.objects.all()
    serializer_class = ImageLabelTypeSerializer


@extend_schema(
    tags=['Image Plans']
)
class DetectionLabelTypeView(BaseLabelTypeView):
    queryset = DetectionLabelType.objects.all()
    serializer_class = DetectionLabelTypeSerializer

@extend_schema(
    tags=['Image Plans']
)
class PolygonLabelTypeView(BaseLabelTypeView):
    queryset = PolygonLabelType.objects.all()
    serializer_class = PolygonLabelTypeSerializer


@extend_schema(
        tags=['Image Plans'],
        description='List all image plans or create a new image plan',
        responses={
            200: ImagePlanSerializer(many=True),
            201: ImagePlanSerializer()
        }
    )
class ImagePlanView(BasePlanListCreateView):
    plan_model = ImagePlan
    serializer_class = ImagePlanSerializer


@extend_schema(
        tags=['Image Plans'],
        description='Get, update, or delete a specific image plan',
        responses={
            200: ImagePlanSerializer(),
            201: ImagePlanSerializer()
        }
    )
class ImagePlanDetailsView(BasePlanDetailsView):
    plan_model = ImagePlan
    serializer_class = ImagePlanSerializer

@extend_schema(
    tags=['Image Plans'],
    description='Upload raw images for a specific image plan',
    request={
        'multipart/form-data': {
            'type': 'object',
            'properties': {
                'file': {
                    'type': 'array',
                    'items': {
                        'type': 'string',
                        'format': 'binary'
                    }
                }
            },
            'required': ['file']
        }
    },
    responses={
        200: ImagePlanRawDataSerializer(many=True),
        201: ImagePlanRawDataSerializer()
    }
)
class ImagePlanRawDataUploadView(BasePlanRawDataListCreateView):
    """
    Handles listing and uploading raw images for a specific Image Batch.
    URL Structure: /projects/<id>/batches/<id>/raw-data/
    """
    plan_model = ImagePlan
    data_model = ImagePlanRawData
    serializer_class = ImagePlanRawDataSerializer


@extend_schema(
    tags=['Image Plans'],
    description='Update quality status of a specific raw image file',
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'quality': {
                    'type': 'string',
                    'enum': ['good', 'bad'],
                    'description': 'Quality status of the image file'
                }
            },
            'required': ['quality']
        }
    },
    responses={
        200: ImagePlanRawDataQualitySerializer,
        400: 'Bad Request',
        404: 'Not Found',
        403: 'Forbidden'
    }
)
class ImagePlanRawDataQualityUpdateView(BasePlanRawDataQualityUpdateView):
    """
    Update quality status of a specific raw image file.
    URL Structure: /projects/<id>/batches/<id>/raw-data/<pk>/quality/
    """
    plan_model = ImagePlan
    data_model = ImagePlanRawData
    serializer_class = ImagePlanRawDataQualitySerializer




