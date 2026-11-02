from django.urls import path

from apps.notifications.views import MarkNotificationAsReadView, NotificationDetailView, NotificationListCreateView

app_name = 'notifications'

urlpatterns = [
    path('', NotificationListCreateView.as_view(), name='notification-list'),
    path('<int:pk>/', NotificationDetailView.as_view(), name='notification-detail'),
    path('<int:pk>/mark-read/', MarkNotificationAsReadView.as_view(), 
         name='mark-notification-read'),
]