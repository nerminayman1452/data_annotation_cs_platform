from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, PolymorphicProxySerializer, OpenApiResponse

from apps.project_management.models import Batch
from apps.project_management.models.annotation_type import AnnotationType
from apps.project_management.models.image_plan import ImagePlan
from apps.project_management.models.text_plan import TextPlan
from apps.project_management.models.audio_plan import AudioPlan

from apps.project_management.serializers.image_plan import ImagePlanSerializer
from apps.project_management.serializers.text_plan import TextPlanSerializer
from apps.project_management.serializers.audio_plan import AudioPlanSerializer

# Model mapping based on plan_type
PLAN_MODELS = {
    'image': ImagePlan,
    'text': TextPlan,
    'audio': AudioPlan,
}

# Serializer mapping based on plan_type
PLAN_SERIALIZERS = {
    'image': ImagePlanSerializer,
    'text': TextPlanSerializer,
    'audio': AudioPlanSerializer,
}

# Sub-type aliases for flexibility and backward compatibility
PLAN_TYPE_ALIASES = {
    'image_object_detection': 'image',
    'image_polygons': 'image',
    'image_classification': 'image',
    'text_labelling': 'text',
    'text_summarization': 'text',
    'text_segmentation': 'text',
    'text_generation': 'text',
    'audio_labelling': 'audio',
    'audio_segmentation': 'audio',
}


def normalize_plan_type(plan_type):
    if not plan_type:
        return ''
    p = str(plan_type).lower().strip()
    return PLAN_TYPE_ALIASES.get(p, p)


def infer_annotation_type(raw_plan_type, plan_category):
    """
    If raw_plan_type contains a specific sub-type (e.g. 'object_detection'),
    resolve or auto-create the corresponding AnnotationType.
    """
    raw_lower = str(raw_plan_type).lower()
    mapping = {
        'object_detection': ('Object Detection', 'IMAGE'),
        'polygons': ('Polygons', 'IMAGE'),
        'classification': ('Classifiication', 'IMAGE'),
        'summarization': ('Summarization', 'TEXT'),
        'segmentation': ('Segmentation', 'TEXT'),
        'labelling': ('Labelling', 'TEXT'),
    }
    for subkey, (name, p_type) in mapping.items():
        if subkey in raw_lower:
            ann = AnnotationType.objects.filter(plan_type=p_type, name__icontains=name[:6]).first()
            if not ann:
                ann, _ = AnnotationType.objects.get_or_create(name=name, plan_type=p_type)
            return ann.id
    return None


class UnifiedPlanView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        plan_type = normalize_plan_type(self.kwargs.get('plan_type', ''))
        return PLAN_SERIALIZERS.get(plan_type, ImagePlanSerializer)

    def get_plan_class_and_serializer(self, plan_type):
        normalized = normalize_plan_type(plan_type)
        if normalized not in PLAN_MODELS:
            return None, None
        return PLAN_MODELS[normalized], PLAN_SERIALIZERS[normalized]

    def get_queryset(self, plan_model=None, batch_id=None):
        if plan_model is None:
            plan_type = self.kwargs.get('plan_type')
            plan_model, _ = self.get_plan_class_and_serializer(plan_type)
            if not plan_model:
                return ImagePlan.objects.none()
        if batch_id is None:
            batch_id = self.kwargs.get('batch_id')
        return plan_model.objects.filter(
            batch__id=batch_id,
            created_by=int(self.request.user.id)
        ).select_related(
            'batch', 'batch__project', 'batch__project__organization'
        ).prefetch_related(
            'config', 'cost_config', 'estimation_config', 'estimation_config__measure_unit'
        )

    @extend_schema(
        tags=['planning'],
        summary='Retrieve plans for a batch',
        description='Retrieve a list of plans for a batch or a single plan detail if plan_id is provided.',
        responses={
            200: PolymorphicProxySerializer(
                component_name='UnifiedPlanResponse',
                serializers={
                    'image': ImagePlanSerializer,
                    'text': TextPlanSerializer,
                    'audio': AudioPlanSerializer,
                },
                resource_type_field_name='plan_type',
            ),
            400: OpenApiResponse(description="Invalid plan type"),
            404: OpenApiResponse(description="Batch or plan not found"),
        }
    )
    def get(self, request, batch_id, plan_type, plan_id=None):
        plan_model, serializer_class = self.get_plan_class_and_serializer(plan_type)
        if not plan_model:
            return Response(
                {"detail": f"Invalid plan type: '{plan_type}'. Must be one of: {list(PLAN_MODELS.keys())}"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        if plan_id:
            # Return single plan detail
            instance = get_object_or_404(plan_model, id=plan_id, batch_id=batch_id, created_by=request.user.id)
            serializer = serializer_class(instance, context={'request': request})
            return Response(serializer.data)
        else:
            # Return list of plans for the batch
            queryset = self.get_queryset(plan_model, batch_id)
            serializer = serializer_class(queryset, many=True, context={'request': request})
            return Response(serializer.data)

    @extend_schema(
        tags=['planning'],
        summary='Create a plan for a batch',
        description='Create a new unified plan (image, text, or audio) for the specified batch.',
        request=PolymorphicProxySerializer(
            component_name='UnifiedPlanCreateRequest',
            serializers={
                'image': ImagePlanSerializer,
                'text': TextPlanSerializer,
                'audio': AudioPlanSerializer,
            },
            resource_type_field_name='plan_type',
        ),
        responses={
            201: PolymorphicProxySerializer(
                component_name='UnifiedPlanCreateResponse',
                serializers={
                    'image': ImagePlanSerializer,
                    'text': TextPlanSerializer,
                    'audio': AudioPlanSerializer,
                },
                resource_type_field_name='plan_type',
            ),
            400: OpenApiResponse(description="Invalid plan type or validation errors"),
            404: OpenApiResponse(description="Batch not found"),
        }
    )
    def post(self, request, batch_id, plan_type):
        normalized_type = normalize_plan_type(plan_type)
        plan_model, serializer_class = self.get_plan_class_and_serializer(normalized_type)
        if not plan_model:
            return Response(
                {"detail": f"Invalid plan type: '{plan_type}'. Must be one of: {list(PLAN_MODELS.keys())}"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        batch = get_object_or_404(Batch, id=batch_id, created_by=request.user.id)
        
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        if 'batch' not in data:
            data['batch'] = batch.id
        if 'annotation_type' not in data:
            inferred_ann = infer_annotation_type(plan_type, normalized_type)
            if inferred_ann:
                data['annotation_type'] = inferred_ann

        serializer = serializer_class(data=data, context={'request': request})
        if serializer.is_valid():
            serializer.save(batch=batch, created_by=int(request.user.id))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=['planning'],
        summary='Update a plan in a batch',
        description='Update an existing plan in a batch by plan_id and plan_type.',
        request=PolymorphicProxySerializer(
            component_name='UnifiedPlanUpdateRequest',
            serializers={
                'image': ImagePlanSerializer,
                'text': TextPlanSerializer,
                'audio': AudioPlanSerializer,
            },
            resource_type_field_name='plan_type',
        ),
        responses={
            200: PolymorphicProxySerializer(
                component_name='UnifiedPlanUpdateResponse',
                serializers={
                    'image': ImagePlanSerializer,
                    'text': TextPlanSerializer,
                    'audio': AudioPlanSerializer,
                },
                resource_type_field_name='plan_type',
            ),
            400: OpenApiResponse(description="Invalid plan type or validation errors"),
            404: OpenApiResponse(description="Plan not found"),
        }
    )
    def put(self, request, batch_id, plan_type, plan_id=None):
        if not plan_id:
            return Response({"detail": "plan_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        plan_model, serializer_class = self.get_plan_class_and_serializer(plan_type)
        if not plan_model:
            return Response({"detail": "Invalid plan type"}, status=status.HTTP_400_BAD_REQUEST)

        instance = get_object_or_404(plan_model, id=plan_id, batch_id=batch_id, created_by=request.user.id)
        serializer = serializer_class(instance, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=['planning'],
        summary='Delete a plan from a batch',
        description='Delete an existing plan from a batch by plan_id and plan_type.',
        responses={
            204: OpenApiResponse(description="Plan deleted successfully"),
            400: OpenApiResponse(description="Invalid plan type or plan_id missing"),
            404: OpenApiResponse(description="Plan not found"),
        }
    )
    def delete(self, request, batch_id, plan_type, plan_id=None):
        if not plan_id:
            return Response({"detail": "plan_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        plan_model, serializer_class = self.get_plan_class_and_serializer(plan_type)
        if not plan_model:
            return Response({"detail": "Invalid plan type"}, status=status.HTTP_400_BAD_REQUEST)

        instance = get_object_or_404(plan_model, id=plan_id, batch_id=batch_id, created_by=request.user.id)
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    tags=['planning'],
    description='Update or delete a specific plan by plan_id and plan_type',
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'title': {'type': 'string'},
                'description': {'type': 'string'},
                'name': {'type': 'string'},
                'annotation_type': {'type': 'string'},
                'is_locked': {'type': 'boolean'},
                'status': {'type': 'string'},
            }
        }
    },
    responses={
        200: {
            'type': 'object',
            'properties': {
                'message': {'type': 'string'},
                'data': {'type': 'object'}
            }
        },
        204: {'description': 'Plan deleted successfully'},
        404: {'description': 'Plan not found'},
        400: {'description': 'Invalid plan_type or validation error'}
    }
)
class UnifiedPlanUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    """
    Unified API endpoint to update or delete plans (text, image, or audio) using plan_id and plan_type.
    
    URL: /plans/<str:plan_type>/<int:plan_id>/
    Methods: GET, PUT, PATCH, DELETE
    
    plan_type can be: 'text', 'image', or 'audio'
    """
    permission_classes = [IsAuthenticated]
    
    def get_plan_model(self):
        """Get the appropriate model based on plan_type from URL kwargs."""
        plan_type = normalize_plan_type(self.kwargs.get('plan_type', ''))
        model = PLAN_MODELS.get(plan_type)
        if not model:
            raise ValueError(f"Invalid plan_type: {plan_type}. Must be 'text', 'image', or 'audio'.")
        return model
    
    def get_serializer_class(self):
        """Get the appropriate serializer based on plan_type."""
        plan_type = normalize_plan_type(self.kwargs.get('plan_type', ''))
        serializer_class = PLAN_SERIALIZERS.get(plan_type)
        if not serializer_class:
            raise ValueError(f"Invalid plan_type: {plan_type}. Must be 'text', 'image', or 'audio'.")
        return serializer_class
    
    def get_queryset(self):
        """Get filtered queryset based on user and plan_type."""
        plan_model = self.get_plan_model()
        return plan_model.objects.filter(
            created_by=int(self.request.user.id)
        ).select_related(
            'batch', 'batch__project', 'batch__project__organization'
        ).prefetch_related(
            'config', 'cost_config', 'estimation_config', 'estimation_config__measure_unit'
        )
    
    def get_object(self):
        """Get the specific plan object by plan_id."""
        plan_id = self.kwargs.get('plan_id')
        queryset = self.get_queryset()
        obj = get_object_or_404(queryset, id=plan_id)
        return obj
    
    def update(self, request, *args, **kwargs):
        """Handle PUT/PATCH requests to update a plan."""
        try:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            serializer = self.get_serializer(
                instance, 
                data=request.data, 
                partial=partial
            )
            serializer.is_valid(raise_exception=True)
            updated_plan = serializer.save()
            
            return Response(
                serializer.data
            , status=status.HTTP_200_OK)
            
        except ValueError as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to update plan: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def destroy(self, request, *args, **kwargs):
        """Handle DELETE requests to remove a plan."""
        try:
            instance = self.get_object()
            plan_type = self.kwargs.get('plan_type', '')
            
            # Optional: Add any pre-deletion checks here
            # For example, check if plan has associated tasks that shouldn't be deleted
            
            instance.delete()
            
            return Response(
                {'message': f'{plan_type} plan deleted successfully'}, 
                status=status.HTTP_204_NO_CONTENT
            )
            
        except ValueError as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to delete plan: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def retrieve(self, request, *args, **kwargs):
        """Handle GET requests to retrieve a plan."""
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            
            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )
            
        except ValueError as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to retrieve plan: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

