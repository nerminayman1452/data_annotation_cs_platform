from django.urls import path

from apps.dashboard.views.batch_join import ApproveBatchAccessAPIView, ListBatchJoinRequestsAPIView, RequestBatchAccessAPIView
from .views.dashboard import AnnotatorDashboardAPIView, BatchDetailsAPIView, MyActiveProgressAPIView, UserStatsAPIView
# from apps.image_annotation.views.task_img_classification import ImageClassificationTasksAPIView, AssignImageClassificationTasksAPIView
from apps.image_annotation.views.annotation_image import NextTaskView, ActiveAssignedTasks, AnnotatorProgressAPIView

urlpatterns = [
    path("batches-group/", AnnotatorDashboardAPIView.as_view(), name="annotator-dashboard"),
    path("batches-group/<int:batch_id>/", BatchDetailsAPIView.as_view(), name="batch-card-details"),
    path("my-active-batches-plans-group/", MyActiveProgressAPIView.as_view(), name="my-active-batches-plans"),
    path("user-stats/", UserStatsAPIView.as_view(), name="annotator-stats"),
    
    path("batches-group/<int:batch_id>/request-access/", RequestBatchAccessAPIView.as_view(), name="request-batch-access"),
    path("join-requests/", ListBatchJoinRequestsAPIView.as_view(), name="list-join-requests"),
    path("join-requests/<int:request_id>/approve/", ApproveBatchAccessAPIView.as_view(), name="approve-batch-access"),
]
