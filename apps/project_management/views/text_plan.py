from apps.project_management.views.plan import BaseLabelTypeView, BasePlanDetailsView, BasePlanListCreateView
from drf_spectacular.utils import OpenApiRequest, extend_schema
# Reusing generic serializers for simple Type models if you have them,
# otherwise you can define simple ModelSerializers for these ViewSets.
from rest_framework import serializers

from apps.project_management.models.text_plan import (
    TextPlan, TextPlanRawData, TextLabelType, TextErrorType, TextSentenceType, TextValidationType
)
from apps.project_management.serializers.text_plan import (
    TextPlanSerializer, TextPlanRawDataSerializer, TextPlanRawDataQualitySerializer
)

from apps.project_management.views.plan_data import BasePlanRawDataListCreateView, BasePlanRawDataQualityUpdateView
from apps.project_management.serializers.text_plan import (
    TextLabelTypeSerializer, TextErrorTypeSerializer, TextSentenceTypeSerializer, TextValidationTypeSerializer
)


# --- Metadata Views ---

@extend_schema(
    tags=['Text Plans'],
    description='Get all text label types',
)
class TextLabelTypeView(BaseLabelTypeView):
    queryset = TextLabelType.objects.all()
    serializer_class = TextLabelTypeSerializer

@extend_schema(
    tags=['Text Plans'],
    description='Get all text error types',
)
class TextErrorTypeView(BaseLabelTypeView):
    queryset = TextErrorType.objects.all()
    serializer_class = TextErrorTypeSerializer

@extend_schema(
    tags=['Text Plans'],
    description='Get all text sentence types',
)
class TextSentenceTypeView(BaseLabelTypeView):
    queryset = TextSentenceType.objects.all()
    serializer_class = TextSentenceTypeSerializer

@extend_schema(
    tags=['Text Plans'],
    description='Get all text validation types',
)
class TextValidationTypeView(BaseLabelTypeView):
    queryset = TextValidationType.objects.all()
    serializer_class = TextValidationTypeSerializer


# --- Main Plan Views ---

@extend_schema(
    tags=['Text Plans'],
    description='List and Create Text Plans',
    responses={
        200: TextPlanSerializer(many=True),
        201: TextPlanSerializer
    }
)
class TextPlanView(BasePlanListCreateView):
    """
    List and Create Text Plans.
    """
    plan_model = TextPlan
    serializer_class = TextPlanSerializer


@extend_schema(
    tags=['Text Plans'],
    description='Retrieve and Update a specific Text Plan',
    responses={
        200: TextPlanSerializer
    }
)
class TextPlanDetailsView(BasePlanDetailsView):
    """
    Retrieve and Update a specific Text Plan.
    """
    plan_model = TextPlan
    serializer_class = TextPlanSerializer


# --- File Upload View (Swagger Compatible) ---
@extend_schema(
    tags=['Text Plans'],
    description='Upload raw text files for a specific Text Plan',
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
    responses=TextPlanRawDataSerializer
)
class TextPlanRawDataUploadView(BasePlanRawDataListCreateView):
    """
    Handles listing and uploading raw text files for a specific Text Plan.
    """
    plan_model = TextPlan
    data_model = TextPlanRawData
    serializer_class = TextPlanRawDataSerializer


@extend_schema(
    tags=['Text Plans'],
    description='Update quality status of a specific raw text file',
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'quality': {
                    'type': 'string',
                    'enum': ['good', 'bad'],
                    'description': 'Quality status of the text file'
                }
            },
            'required': ['quality']
        }
    },
    responses={
        200: TextPlanRawDataQualitySerializer,
        400: 'Bad Request',
        404: 'Not Found',
        403: 'Forbidden'
    }
)
class TextPlanRawDataQualityUpdateView(BasePlanRawDataQualityUpdateView):
    """
    Update quality status of a specific raw text file.
    URL Structure: /projects/<id>/batches/<id>/raw-data/<pk>/quality/
    """
    plan_model = TextPlan
    data_model = TextPlanRawData
    serializer_class = TextPlanRawDataQualitySerializer