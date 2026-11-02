from django.urls import path

from apps.tasks.views.task_generator import (
    GeneratePlanTasksAPIView,
    PlanTaskListView,
    PlanTaskDetailView,
)


urlpatterns = [
    path("plans/generate-tasks/", GeneratePlanTasksAPIView.as_view(), name="generate-plan-tasks"),
    path("plans/<int:plan_id>/<str:plan_type>/tasks/", PlanTaskListView.as_view(), name="plan-tasks-list"),
    path("plans/<int:plan_id>/<str:plan_type>/tasks/<int:task_id>/", PlanTaskDetailView.as_view(), name="plan-task-detail"),
]
