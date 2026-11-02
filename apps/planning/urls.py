from django.urls import path
from rest_framework import routers

from apps.planning.views.measure_unit import MeasureUnitsView
from apps.planning.views.Estimation import BatchEstimationView
from apps.planning.views.plan_graph import plan_graph_view
from apps.planning.views.unified_plan import UnifiedPlanView, UnifiedPlanUpdateDeleteView


router = routers.DefaultRouter()
router.register(r'measure_units', MeasureUnitsView)


urlpatterns = [
    path('measure-units/', MeasureUnitsView.as_view({'get': 'list', 'post': 'create'}), name='measure_units_list_create'),
    path('measure-units/<int:pk>/', MeasureUnitsView.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='measure_unit_detail'),

    path("batches/<int:batch_id>/plans/<str:plan_type>/", UnifiedPlanView.as_view(), name="unified_plan_list_create"),
    # path("batches/<int:batch_id>/plans/<str:plan_type>/<int:plan_id>/", UnifiedPlanView.as_view(), name="unified_plan_detail"),

    # Unified plan update/delete endpoints
    path('plans/<str:plan_type>/<int:plan_id>/', UnifiedPlanUpdateDeleteView.as_view(),
         name='unified-plan-update-delete'),

    #todo
    # path('projects/<int:project_id>/', ProjectEstimationView.as_view(), name='project_estimation'),
    
    #todo
    path('batches/<int:batch_id>/', BatchEstimationView.as_view(), name='batch_estimation'),
    # path('batches/<int:batch_id>/approve/', BatchEstimationView.as_view(), name='approval_estimation'),
    
    # Plan Graph API
    path('plans/<int:plan_id>/graph/', plan_graph_view, name='plan-graph'),
]
