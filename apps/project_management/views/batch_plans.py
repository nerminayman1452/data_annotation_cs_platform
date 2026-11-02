from rest_framework import viewsets, mixins, permissions
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import Http404

from apps.project_management.models.batch import Batch
from apps.project_management.serializers.batch import BatchPlansSerializer
from apps.planning.services.graph import GraphHandler


@extend_schema(tags=['Batches'])
class BatchPlansViewSet(mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    ViewSet for retrieving batches with their associated plans.
    Provides a unified endpoint to access all plan types (Text, Image, Audio) 
    associated with batches. Each plan includes PlanResponseMixin fields.
    """
    serializer_class = BatchPlansSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Batch.objects.select_related('project').prefetch_related(
        'textplan__config',
        'textplan__estimation_config', 
        'textplan__cost_config',
        'imageplan__config',
        'imageplan__estimation_config',
        'imageplan__cost_config',
        'audioplan__config',
        'audioplan__estimation_config',
        'audioplan__cost_config'
    ).all()
    
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['project_id', 'is_approved', 'status']

    @extend_schema(
        summary="List batches with their plans",
        description="Retrieve a list of batches with all associated text, image, and audio plans. Each plan includes comprehensive details from PlanResponseMixin.",
        responses={200: BatchPlansSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        """
        List all batches with their associated plans.
        Supports filtering by project_id, is_approved, and status.
        Each plan includes all PlanResponseMixin fields like progress, quality, costs, etc.
        """
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Retrieve batch with plans",
        description="Retrieve a specific batch with all associated text, image, and audio plans. Each plan includes comprehensive details from PlanResponseMixin.",
        responses={200: BatchPlansSerializer}
    )
    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve a specific batch with all associated plans.
        Each plan includes all PlanResponseMixin fields like progress, quality, costs, etc.
        """
        return super().retrieve(request, *args, **kwargs)

    # @extend_schema(
    #     summary="Get batch cost graph data",
    #     description="Generate line chart data showing planned vs actual vs estimated costs over time for a batch",
    #     responses={200: {
    #         'type': 'object',
    #         'properties': {
    #             'labels': {'type': 'array', 'items': {'type': 'string'}},
    #             'planned_cost': {'type': 'object'},
    #             'actual_cost': {'type': 'object'},
    #             'estimated_cost': {'type': 'object'}
    #         }
    #     }}
    # )
    # @action(methods=['get'], detail=True, url_path='graph')
    # def batch_graph(self, request, *args, **kwargs):
    #     """
    #     Generate cost tracking graph data for a specific batch.
        
    #     URL: /project-management/batches-performance/{batch_id}/graph/
        
    #     Returns line chart data with three lines:
    #     - planned_cost: Expected cost trajectory
    #     - actual_cost: Actual cost incurred so far
    #     - estimated_cost: Future cost projection based on current trends
    #     """
    #     batch = self.get_object()
    #     if not batch:
    #         raise Http404("Batch not found")
        
    #     chart = GraphHandler()
    #     data = chart.batch_line_chart_data(batch)
        
    #     return Response(data)

    def get_queryset(self):
        """
        Optimize queryset based on user permissions and requested action
        """
        queryset = super().get_queryset()
        
        # Filter by user ownership if needed
        user = self.request.user
        if not user.is_superuser:
            # Only show batches created by the user or where user has access
            queryset = queryset.filter(created_by=user.id)
        
        return queryset
