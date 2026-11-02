from rest_framework import viewsets, mixins, permissions
from drf_spectacular.utils import extend_schema

from apps.project_management.models.batch import Batch
from apps.project_management.models.project import Project
from apps.project_management.serializers.stats import BatchPlanStatsSerializer, ProjectBatchStatsSerializer


@extend_schema(tags=['Batches'])
class BatchPlanStatsViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    Retrieve Batch instance statistics.
    
    Provides comprehensive statistics for all plans within a batch,
    including totals and averages for units, costs, progress, and quality metrics.
    """
    queryset = Batch.objects.all()
    serializer_class = BatchPlanStatsSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_url_kwarg = 'batch_id'

    def get_queryset(self):
        """
        Filter batches based on user permissions.
        Only show batches created by the user or where user has access.
        """
        queryset = super().get_queryset()
        user = self.request.user
        
        if not user.is_superuser:
            # Only show batches created by the user
            queryset = queryset.filter(created_by=user.id)
        
        return queryset

    @extend_schema(
        summary="Get batch statistics",
        description="Retrieve comprehensive statistics for a specific batch including totals and averages of all associated plans",
        responses={200: BatchPlanStatsSerializer}
    )
    def retrieve(self, request, *args, **kwargs):
        """
        Get detailed statistics for a batch.
        
        Returns:
        - Total units, costs, progress, quality across all plans
        - Average values per plan
        - Duration estimates
        - Budget vs actual costs
        """
        return super().retrieve(request, *args, **kwargs)


@extend_schema(tags=['Projects'])
class ProjectBatchStatsViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    Retrieve Project instance statistics.
    
    Provides comprehensive statistics for all batches within a project,
    including totals and averages for units, costs, progress, and quality metrics.
    """
    queryset = Project.objects.all()
    serializer_class = ProjectBatchStatsSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_url_kwarg = 'project_id'

    def get_queryset(self):
        """
        Filter projects based on user permissions.
        Only show projects created by the user or where user has access.
        """
        queryset = super().get_queryset()
        user = self.request.user
        
        if not user.is_superuser:
            # Only show projects created by the user
            queryset = queryset.filter(created_by=user.id)
        
        return queryset

    @extend_schema(
        summary="Get project statistics", 
        description="Retrieve comprehensive statistics for a specific project including totals and averages of all associated batches",
        responses={200: ProjectBatchStatsSerializer}
    )
    def retrieve(self, request, *args, **kwargs):
        """
        Get detailed statistics for a project.
        
        Returns:
        - Total units, costs, progress, quality across all batches
        - Average values per batch
        - Duration estimates
        - Budget vs actual costs
        - Batch count
        """
        return super().retrieve(request, *args, **kwargs)
