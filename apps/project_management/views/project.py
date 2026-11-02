from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from django.db.models import Prefetch, Count, Sum, F, Q, DecimalField
from django.db.models.functions import Coalesce

from apps.project_management.models import Batch, ImagePlan, TextPlan
from apps.project_management.models.batch import BatchEstimates, BatchActuals

from apps.project_management.models import Project, Organization
from apps.project_management.serializers.project import ProjectSerializer


class BaseProjectView:
    """
    Shared Logic for Project Views.
    Includes permissions and QuerySet optimization.
    """
    permission_classes = [IsAuthenticated]

    def get_optimized_queryset(self):
        """
        Prefetches the hierarchy (Project -> Batch -> Plan -> Configs)
        so that 'estimates' and 'actuals' properties are calculated in memory.
        """

        
        
        # Prefetch plans with their related data
        image_plans = ImagePlan.objects.select_related(
            'estimation_config', 
            'cost_config',
            'batch',
            'batch__project'
        ).prefetch_related('raw_data_files')
        
        text_plans = TextPlan.objects.select_related(
            'estimation_config', 
            'cost_config',
            'batch',
            'batch__project'
        ).prefetch_related('raw_data_files')
        
        # Prefetch batches with their plans and related data
        batches = Batch.objects.select_related(
            'project',
            'project__organization'
        ).prefetch_related(
            Prefetch('imageplan', queryset=image_plans),
            Prefetch('textplan', queryset=text_plans)
        )
        
        # Main queryset with prefetched relationships
        projects = Project.objects.select_related('organization').prefetch_related(
            Prefetch('batches', queryset=batches, to_attr='_prefetched_batches')
        )
        
        # Annotate projects with the actual plans count and basic fields
        projects = projects.annotate(
            actual_plans_count=Count('batches__imageplan', distinct=True) + Count('batches__textplan', distinct=True),
            total_units=Sum(
                Coalesce('batches__imageplan__estimation_config__total_units', 0) + 
                Coalesce('batches__textplan__estimation_config__total_units', 0),
                distinct=True,
                output_field=DecimalField()
            )
        )
        
        # Ensure we have all the necessary prefetches for the actuals calculations
        projects = projects.prefetch_related(
            Prefetch('batches__imageplan__estimation_config', to_attr='prefetched_estimation_config'),
            Prefetch('batches__textplan__estimation_config', to_attr='prefetched_estimation_config'),
            Prefetch('batches__imageplan__cost_config', to_attr='prefetched_cost_config'),
            Prefetch('batches__textplan__cost_config', to_attr='prefetched_cost_config'),
            'batches__imageplan__raw_data_files',
            'batches__textplan__raw_data_files',
        )
        
        # Calculate efforts in Python since it's a property/method
        for project in projects:
            total_efforts = 0
            for batch in project._prefetched_batches:
                for plan in batch.get_all_plans():
                    if hasattr(plan, 'estimation_config'):
                        total_efforts += getattr(plan.estimation_config, 'efforts', 0)
            setattr(project, '_total_efforts', total_efforts)
        
        return projects

# --- Write View ---

@extend_schema(
    tags=['Projects'],
    description='List all projects or create a new project',
    parameters=[
        OpenApiParameter(
            name='organization_id',
            type=int,
            location=OpenApiParameter.QUERY,
            description='Filter projects by organization ID',
            required=False
        )
    ],
    responses={
        200: ProjectSerializer(many=True),
        201: ProjectSerializer()
    }
)
class ListCreateProjectView(BaseProjectView, generics.ListCreateAPIView):
    """
    POST: Create a new project
    GET: List all projects (optionally filtered by organization_id)
    """
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = self.get_optimized_queryset()
        organization_id = self.request.query_params.get('organization_id')
        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)
        return queryset.all()


# --- Read Views ---

@extend_schema(
    tags=['Projects'],
)
class ProjectListOwnerView(BaseProjectView, generics.ListAPIView):
    """
    GET: List projects owned by the user (via Organization)
    """
    serializer_class = ProjectSerializer

    def get_queryset(self):
        user = self.request.user
        # Filter projects where the organization is owned by the logged-in user
        return self.get_optimized_queryset().filter(organization__created_by=user.id)

@extend_schema(
    tags=['Projects'],
)
class ActiveProjectListView(BaseProjectView, generics.ListAPIView):
    """
    GET: List all active (non-archived) projects
    """
    serializer_class = ProjectSerializer

    def get_queryset(self):
        return self.get_optimized_queryset().filter(is_archived=False)


@extend_schema(
    tags=['Projects'],
)
class ProjectDetailView(BaseProjectView, generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve specific project details
    PUT/PATCH: Update project details
    DELETE: Archive/Delete project
    """
    serializer_class = ProjectSerializer  # For Reads
    lookup_field = 'id'

    def get_serializer_class(self):
        # Use CreateSerializer for Updates (Write), ProjectSerializer for Reads
        if self.request.method in ['PUT', 'PATCH']:
            return ProjectSerializer
        return ProjectSerializer

    def get_queryset(self):
        return self.get_optimized_queryset().all()
