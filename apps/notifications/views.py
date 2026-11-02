from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Notification, NotificationService
from .serializers import NotificationSerializer

class NotificationListCreateView(generics.ListCreateAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class NotificationDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'pk'

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

class MarkNotificationAsReadView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    
    def update(self, request, *args, **kwargs):
        notification = self.get_object()
        notification.mark_as_read()
        return Response(
            {'status': 'notification marked as read'}, 
            status=status.HTTP_200_OK
        )
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user, is_read=False)
