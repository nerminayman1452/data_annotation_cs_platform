from rest_framework import generics, viewsets
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

class BaseLabelTypeView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    # Must be defined in subclass
    queryset = None
    serializer_class = None

class BasePlanListCreateView(generics.ListCreateAPIView):
    """
    List plans for a batch & create a new plan.
    Optimized for Namespace Pattern (estimates/actuals).
    """
    permission_classes = [IsAuthenticated]
    plan_model = None
    serializer_class = None

    def get_queryset(self):
        # 1. Start with base queryset
        queryset = self.plan_model.objects.filter(
            created_by=int(self.request.user.id)
        )

        # 2. OPTIMIZATION: Select related forward FKs and prefetch reverse OneToOne/M2M
        # This makes properties like plan.estimates.total_cost essentially free
        queryset = queryset.select_related(
            'batch', 
            'batch__project', 
            'batch__project__organization'
        ).prefetch_related(
            'config', 'cost_config', 'estimation_config', 'estimation_config__measure_unit'
        )

        # 3. Filter by batch_id if provided (accept via query param or URL kwarg)
        batch_id = self.kwargs.get('batch_id') or self.request.query_params.get('batch_id')
        if batch_id:
            try:
                batch_id = int(batch_id)
            except (TypeError, ValueError):
                batch_id = None

        if batch_id:
            queryset = queryset.filter(batch__id=batch_id)  # Note: batch__id, not project__id

        return queryset
    
    def perform_create(self, serializer):
        serializer.save(created_by=int(self.request.user.id))

class BasePlanDetailsView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    plan_model = None
    serializer_class = None

    def get_queryset(self):
        # Apply same optimizations for Detail view
        return self.plan_model.objects.select_related(
            'batch', 'batch__project', 'batch__project__organization'
        ).prefetch_related('config', 'cost_config', 'estimation_config').filter(
            created_by=int(self.request.user.id)
        )

    def get_object(self):
        # Adjust based on your URL conf (usually uses 'pk')
        return get_object_or_404(
            self.get_queryset(),
            id=int(self.kwargs.get("pk", self.kwargs.get("plan_id")))
        )