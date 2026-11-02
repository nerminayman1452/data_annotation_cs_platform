from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample

from apps.project_management.models.organization import Organization
from apps.project_management.serializers.organization import OrganizationSerializer


@extend_schema(
    tags=['Organizations'],
    description='List all organizations or create a new organization',
    responses={
        200: OrganizationSerializer(many=True),
        201: OrganizationSerializer()
    }
)
class OrganizationListCreateView(generics.ListCreateAPIView):
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Organization.objects.filter(created_by=self.request.user.id)

@extend_schema(
    tags=['Organizations'],
    description='Retrieve, update, or delete an organization',
    responses={
        200: OrganizationSerializer(),
        204: None
    }
)
class OrganizationDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Organization.objects.filter(created_by=self.request.user.id)
