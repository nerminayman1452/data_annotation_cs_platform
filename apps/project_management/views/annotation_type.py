from collections import defaultdict

from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample


from apps.project_management.models.annotation_type import AnnotationType
from apps.project_management.serializers.annotation_type import AnnotationTypeSerializer



@extend_schema(
        tags=['Annotation Types'],
        description='List all annotation types or create a new annotation type',
        responses={
            200: AnnotationTypeSerializer(many=True),
            201: AnnotationTypeSerializer()
        }
    )
# CHANGE: Inherit from 'ModelViewSet' instead of 'ReadOnlyModelViewSet'
class AnnotationTypeViewSet(viewsets.ModelViewSet):
    """
    Full CRUD API for Annotation Types.
    """
    queryset = AnnotationType.objects.all().order_by('plan_type', 'name')
    serializer_class = AnnotationTypeSerializer

    # Filter/Search capabilities
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['plan_type']  # e.g. ?plan_type=TEXT
    search_fields = ['name']  # e.g. ?search=bounding

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        serializer = self.get_serializer(queryset, many=True)

        grouped = defaultdict(list)

        for item, obj in zip(serializer.data, queryset):
            grouped[obj.plan_type].append(item)

        return Response(grouped)