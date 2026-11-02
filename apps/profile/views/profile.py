from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from ..models.profile import Profile
from ..serializers.profile import ProfileSerializer

@extend_schema(
        tags=['Profile']
    )
class ProfileViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing profile instances.
    """
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]
    queryset = Profile.objects.all()
    lookup_field = 'id'

    def get_queryset(self):
        """
        Optionally filter profiles by role if 'role' query parameter is provided.
        """
        queryset = Profile.objects.all()
        role = self.request.query_params.get('role', None)
        if role is not None:
            queryset = queryset.filter(role=role)
        return queryset

    def perform_create(self, serializer):
        serializer.save()

    def perform_update(self, serializer):
        serializer.save()

    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        Return the current user's profile.
        """
        try:
            profile = Profile.objects.get(user_id=request.user.id)
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        except Profile.DoesNotExist:
            return Response(
                {"detail": "Profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )
