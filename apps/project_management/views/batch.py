from rest_framework import generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from django.http import Http404

from apps.project_management.models.batch import Batch
from apps.project_management.serializers.batch import BatchSerializer, BatchCreateSerializer
from apps.planning.services.graph import GraphHandler



class BaseBatchView:
    permission_classes = [permissions.IsAuthenticated]

    def get_optimized_queryset(self):
        """
        Deep prefetch to allow efficient calculation of 'estimates' properties.
        """
        return Batch.objects.select_related('project').prefetch_related(
            # Prefetch specific plan types and their configs
            'imageplan__estimation_config', 'imageplan__cost_config', 
            'imageplan__raw_data_files', # For actual counts
            
            'textplan__estimation_config', 'textplan__cost_config',
            'textplan__raw_data_files',
            
            'audioplan__estimation_config', 'audioplan__cost_config',
            # Add other plans...
        )

@extend_schema(
        tags=['Batches'],
        description='List all batches or create a new batch',
        responses={
            200: BatchSerializer(many=True),
            201: BatchSerializer()
        }
    )
class BatchListCreateView(BaseBatchView, generics.ListCreateAPIView):
    """
    GET: List Batches (Optimized)
    POST: Create Batch
    """
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return BatchCreateSerializer
        return BatchSerializer

    def get_queryset(self):
        user_id = self.request.user.id
        
        # Optional: Filter by project_id in URL query
        project_id = self.request.query_params.get('project_id')
        
        queryset = self.get_optimized_queryset().filter(created_by=user_id)
        
        if project_id:
            queryset = queryset.filter(project_id=project_id)
            
        return queryset


@extend_schema(
        tags=['Batches'],
        description='Get, update, or delete a specific batch',
        responses={
            200: BatchSerializer(),
            201: BatchSerializer()
        }
    )
class BatchDetailsView(BaseBatchView, generics.RetrieveUpdateDestroyAPIView):
    """
    GET, PUT, PATCH, DELETE specific Batch
    """
    # Model uses `id` as the primary key; keep URL kwarg `batch_id` for routes
    lookup_field = 'id'
    lookup_url_kwarg = 'batch_id'
                
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return BatchCreateSerializer
        return BatchSerializer

    def get_queryset(self):
        return self.get_optimized_queryset().filter(created_by=self.request.user.id)


# class BatchTemplateListView(BaseBatchView, generics.ListAPIView):
#     """
#     GET: List Batch Templates
#     """
#     def get_serializer_class(self):
#         return BatchSerializer

#     def get_queryset(self):
#         return self.get_optimized_queryset().filter(is_template=True)


@extend_schema(
    tags=['Batches'],
    description='List Batches for a specific project',
    responses={
        200: BatchSerializer(many=True)
    }
)
class ProjectBatchListView(BaseBatchView, generics.ListAPIView):
    """
    GET: List Batches for a specific project
    """
    def get_serializer_class(self):
        return BatchSerializer

    def get_queryset(self):
        project_id = self.kwargs.get('project_id')
        return self.get_optimized_queryset().filter(project_id=project_id)


@extend_schema(
    tags=['Batches'],
    summary="Get all plans for a specific batch",
    description="Retrieve all text, image, and audio plans for a specific batch ID. Each plan includes comprehensive details from PlanResponseMixin.",
    responses={200: {"type": "array", "items": {"type": "object"}}}
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def batch_plans_detail(request, batch_id):
    """
    Get all plans for a specific batch.
    
    URL: /project-management/batches/{batch_id}/plans/
    
    Returns all text, image, and audio plans associated with the batch.
    Each plan includes all PlanResponseMixin fields like progress, quality, costs, etc.
    """
    try:
        batch = Batch.objects.select_related('project').prefetch_related(
            'textplan__config',
            'textplan__estimation_config', 
            'textplan__cost_config',
            'imageplan__config',
            'imageplan__estimation_config',
            'imageplan__cost_config',
            'audioplan__config',
            'audioplan__estimation_config',
            'audioplan__cost_config'
        ).get(id=batch_id)
        
        # Check user permissions
        user = request.user
        if batch.created_by != int(user.id):
            return Response(
                {"error": "You do not have permission to view plans for this batch."}, 
                status=403
            )
        
        # Get all plans using the batch's get_all_plans method
        all_plans = batch.get_all_plans()
        
        # Filter out normal plans if needed
        filtered_plans = [plan for plan in all_plans if not getattr(plan, 'normal_plan', False)]
        
        plans_data = []
        
        for plan in filtered_plans:
            # Use the appropriate serializer based on plan type
            if plan.__class__.__name__ == 'TextPlan':
                from apps.project_management.serializers.text_plan import TextPlanSerializer
                serializer = TextPlanSerializer(plan, context={'request': request})
                data = serializer.data
                data['plan_type'] = 'text'
            elif plan.__class__.__name__ == 'ImagePlan':
                from apps.project_management.serializers.image_plan import ImagePlanSerializer
                serializer = ImagePlanSerializer(plan, context={'request': request})
                data = serializer.data
                data['plan_type'] = 'image'
            elif plan.__class__.__name__ == 'AudioPlan':
                from apps.project_management.serializers.audio_plan import AudioPlanSerializer
                serializer = AudioPlanSerializer(plan, context={'request': request})
                data = serializer.data
                data['plan_type'] = 'audio'
            else:
                # Fallback for any other plan types
                data = {
                    'id': plan.id,
                    'plan_type': plan.__class__.__name__.lower().replace('plan', ''),
                    'title': getattr(plan, 'name', ''),
                    'description': getattr(plan, 'description', ''),
                    'status': getattr(plan, 'status', ''),
                }
            
            plans_data.append(data)
        
        return Response(plans_data)
        
    except Batch.DoesNotExist:
        return Response(
            {"error": f"Batch with ID {batch_id} not found."}, 
            status=404
        )
    except Exception as e:
        return Response(
            {"error": f"An error occurred: {str(e)}"}, 
            status=500
        )


@extend_schema(
    tags=['Batches'],
    summary="Get plan cost graph data",
    description="Generate line chart data showing planned vs actual vs estimated costs over time for a specific plan",
    responses={200: {
        'type': 'object',
        'properties': {
            'labels': {'type': 'array', 'items': {'type': 'string'}},
            'planned_cost': {'type': 'object'},
            'actual_cost': {'type': 'object'},
            'estimated_cost': {'type': 'object'}
        }
    }}
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def plan_graph_detail(request, batch_id, plan_id):
    """
    Generate cost tracking graph data for a specific plan within a batch.
    
    URL: /project-management/batches/{batch_id}/plans/{plan_id}/graph/
    
    Returns line chart data with three lines:
    - planned_cost: Expected cost trajectory
    - actual_cost: Actual cost incurred so far  
    - estimated_cost: Future cost projection based on current trends
    """
    try:
        # First verify user has access to the batch
        batch = Batch.objects.get(id=batch_id)
        user = request.user
        if batch.created_by != int(user.id):
            return Response(
                {"error": "You do not have permission to view plans for this batch."}, 
                status=403
            )
        
        # Get all plans and find the specific one
        all_plans = batch.get_all_plans()
        target_plan = None
        
        for plan in all_plans:
            if plan.id == plan_id:
                target_plan = plan
                break
        
        if not target_plan:
            return Response(
                {"error": f"Plan with ID {plan_id} not found in this batch."}, 
                status=404
            )
        
        # Generate graph data
        chart = GraphHandler()
        data = chart.plan_line_chart_data(target_plan)
        
        return Response(data)
        
    except Batch.DoesNotExist:
        return Response(
            {"error": f"Batch with ID {batch_id} not found."}, 
            status=404
        )
    except Exception as e:
        return Response(
            {"error": f"An error occurred: {str(e)}"}, 
            status=500
        )
