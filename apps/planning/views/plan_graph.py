from rest_framework import permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from apps.project_management.models.batch import Batch
from apps.planning.services.graph import GraphHandler


@extend_schema(
    tags=['planning'],
    summary="Get plan cost graph data",
    description="Generate line chart data showing planned vs actual vs estimated costs over time for a specific plan",
    responses={200: {
        'type': 'object',
        'properties': {
            'labels': {'type': 'array', 'items': {'type': 'string'}},
            'planned_cost': {'type': 'number'},
            'actual_cost': {'type': 'number'},
            'estimated_cost': {'type': 'number'}
        }
    }}
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def plan_graph_view(request, plan_id):
    """
    Generate cost tracking graph data for a specific plan.
    
    URL: /planning/plans/{plan_id}/graph/
    
    Returns line chart data with three values:
    - planned_cost: Expected total cost
    - actual_cost: Actual cost incurred so far  
    - estimated_cost: Future cost projection based on current trends
    """
    try:
        # Find the plan across all batches
        target_plan = None
        user_batches = Batch.objects.filter(created_by=request.user.id)
        
        for batch in user_batches:
            all_plans = batch.get_all_plans()
            for plan in all_plans:
                if plan.id == plan_id:
                    target_plan = plan
                    break
            if target_plan:
                break
        
        if not target_plan:
            return Response(
                {"error": f"Plan with ID {plan_id} not found or you don't have permission to access it."}, 
                status=404
            )
        
        # Generate graph data
        chart = GraphHandler()
        data = chart.plan_line_chart_data(target_plan)
        
        return Response(data)
        
    except Exception as e:
        return Response(
            {"error": f"An error occurred: {str(e)}"}, 
            status=500
        )
