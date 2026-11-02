
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.planning.models.measure_unit import MeasureUnits
from apps.planning.serializers.measure_unit import MeasureUnitsSerializer

@extend_schema_view(
    list=extend_schema(description='Retrieve a list of Measure Unit instances.'),
    create=extend_schema(description='Create a new Measure Unit instance.'),
    retrieve=extend_schema(description='Retrieve a specific Measure Unit instance.'),
    update=extend_schema(description='Update an existing Measure Unit instance.'),
    partial_update=extend_schema(description='Partially update an existing Measure Unit instance.'),
    destroy=extend_schema(description='Delete a Measure Unit instance.')
)
class MeasureUnitsView(viewsets.ModelViewSet):
    serializer_class = MeasureUnitsSerializer
    permission_classes = [IsAuthenticated]
    queryset = MeasureUnits.objects.all()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user.id)

# class MeasureUnitsView(generics.ListCreateAPIView):
#     permission_classes = [IsAuthenticated, IsAdminUser]

#     queryset = MeasureUnits.objects.all()
#     serializer_class = MeasureUnitsSerializer