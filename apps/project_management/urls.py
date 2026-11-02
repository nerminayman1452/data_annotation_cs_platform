from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.project_management.views.annotation_type import AnnotationTypeViewSet
from apps.project_management.views.batch import BatchListCreateView, BatchDetailsView, ProjectBatchListView, batch_plans_detail, plan_graph_detail
from apps.project_management.views.batch_plans import BatchPlansViewSet
from apps.project_management.views.stats import BatchPlanStatsViewSet, ProjectBatchStatsViewSet
# from apps.project_management.views.image_batch_data import ImageBatchDataUploadView
from apps.project_management.views.image_plan import ImagePlanDetailsView, ImagePlanRawDataUploadView, ImagePlanView, ImagePlanRawDataQualityUpdateView
from apps.project_management.views.invitation import (
    PlanInvitationCreateView, 
    PlanInvitationListView, 
    PlanInvitationResponseView,
    BulkPlanInvitationCreateView
    
)   
from apps.project_management.views.organization import OrganizationListCreateView, OrganizationDetailView
# from apps.project_management.views.batch import BatchView
from apps.project_management.views.plan_members import ImagePlanMemberDetailView, ImagePlanMembersView, \
    TextPlanMemberDetailView, TextPlanMembersView
from apps.project_management.views.project import ProjectDetailView, ProjectListOwnerView, \
    ActiveProjectListView, ListCreateProjectView
from apps.project_management.views.template import BatchCreateFromTemplateView, TextPlanCreateReuseView, ImagePlanCreateReuseView, BatchTemplateListView
from apps.project_management.views.text_plan import TextPlanDetailsView, TextPlanRawDataUploadView, TextPlanView, TextPlanRawDataQualityUpdateView
from apps.project_management.views.plan_data import UnifiedPlanRawDataQualityUpdateView, UnifiedPlanRawDataUploadView

# 1. Create a router
router = DefaultRouter()

router.register(r'annotation-types', AnnotationTypeViewSet)
router.register(r'batches-performance', BatchPlansViewSet)
router.register(r'batch/stats', BatchPlanStatsViewSet, basename='batch-stats')
router.register(r'project/stats', ProjectBatchStatsViewSet, basename='project-stats')

urlpatterns = [

    ###ORGANIZATION###
    path("organizations/", OrganizationListCreateView.as_view(), name="create_list_organization"),
    path("organizations/<int:id>/", OrganizationDetailView.as_view(), name="organization_details"),


    ###PROJECT###
    path("projects/", ListCreateProjectView.as_view(), name="create_list_project"),
    path('projects/<int:id>/', ProjectDetailView.as_view(), name='project_details'),
    
    path("organization-projects-list/", ProjectListOwnerView.as_view(), name="owner's_projects"),
    path("active-projects/", ActiveProjectListView.as_view(), name="all_active_projects"),

    ###BATCH###
    path('batches/', BatchListCreateView.as_view(), name='batches_list'),
    path('batches/<int:batch_id>/', BatchDetailsView.as_view(), name='batch-details'),
    path('batches/<int:batch_id>/plans/', batch_plans_detail, name='batch-plans-detail'),
    path('batches/<int:batch_id>/plans/<int:plan_id>/graph/', plan_graph_detail, name='plan-graph-detail'),
    path('batches/template/', BatchCreateFromTemplateView.as_view(), name='batch-create-template'),
    path('batches/template/list/', BatchTemplateListView.as_view(), name='batch-template-list'),
    path('<int:project_id>/batches/', ProjectBatchListView.as_view(), name='project-batches-list'),

    # ----------------image-plan endpoints----------------
    path('image-plan/', ImagePlanView.as_view(), name='create-image-plan'),
    path('image-plan/<int:batch_id>/plans/', ImagePlanView.as_view(), name='list-image-plans'),
    path('image-plan/<int:plan_id>/', ImagePlanDetailsView.as_view(),
         name='image-plan-details'),

    path(
        'image-plan/<int:plan_id>/raw-data/',
        ImagePlanRawDataUploadView.as_view(),
        name='plan-raw-data-list-create'
    ),

    #update quality of raw data
    path('image-plan/raw-data/<int:pk>/quality/', ImagePlanRawDataQualityUpdateView.as_view(), name='image-plan-raw-data-quality-update'),
    
    path('image-plan/reuse/', ImagePlanCreateReuseView.as_view(), name='plan-create-reuse'),

    path('image-plan/<int:plan_id>/members/', ImagePlanMembersView.as_view(), name='image-plan-members'),
    path('image-plan/<int:plan_id>/members/<int:pk>/', ImagePlanMemberDetailView.as_view(),
         name='image-plan-member-detail'),

    # ----------------text-plan endpoints----------------
    path('text-plan/', TextPlanView.as_view(), name='create-text-plan'),
    path('text-plan/<int:batch_id>/plans/', TextPlanView.as_view(), name='list-text-plans'),
    path('text-plan/<int:plan_id>/', TextPlanDetailsView.as_view(),
         name='text-plan-details'),
    path(
        'text-plan/<int:plan_id>/raw-data/',
        TextPlanRawDataUploadView.as_view(),
        name='text-plan-raw-data-list-create'
    ),

    #update quality of raw data
    path('text-plan/raw-data/<int:pk>/quality/', TextPlanRawDataQualityUpdateView.as_view(), name='text-plan-raw-data-quality-update'),

    path('text-plan/reuse/', TextPlanCreateReuseView.as_view(), name='plan-create-reuse'),

    path('text-plan/<int:plan_id>/members/', TextPlanMembersView.as_view(), name='text-plan-members'),
    path('text-plan/<int:plan_id>/members/<int:pk>/', TextPlanMemberDetailView.as_view(),
         name='text-plan-member-detail'),

    # # ----------------audio-plan endpoints----------------
    # path('audio-plan/', AudioPlanView.as_view(), name='create-audio-plan'),
    # path('audio-plan/<int:batch_id>/plans/', AudioPlanView.as_view(), name='list-audio-plans'),
    # path('audio-plan/<int:plan_id>/', AudioPlanDetailsView.as_view(),
    #      name='audio-plan-details'),
    # path(
    #     'audio-plan/<int:plan_id>/raw-data/',
    #     AudioPlanRawDataUploadView.as_view(),
    #     name='audio-plan-raw-data-list-create'
    # ),

    #-----------------Unified plan endpoints------------------------

    # Unified raw-data upload endpoint that accepts plan type in path
    path(
        'plan/<str:plan_type>/<int:plan_id>/raw-data/',
        UnifiedPlanRawDataUploadView.as_view(),
        name='plan-raw-data-unified'
    ),

    # Unified raw-data quality-update endpoint that accepts plan type in path
    path(
        'plan/<str:plan_type>/raw-data/<int:pk>/quality/',
        UnifiedPlanRawDataQualityUpdateView.as_view(),
        name='plan-raw-data-quality-unified'
    ),

    # Invitation endpoints
    # path('batches/<int:batch_id>/invite/', BatchInvitationCreateView.as_view(), name='batch_invite'),
    # path('batches/<int:batch_id>/invitations/', BatchInvitationListView.as_view(), name='batch_invitations_list'),
    # path('invitations/respond/', BatchInvitationResponseView.as_view(), name='invitation_respond'),

    # Create single invitation
    path('plans/invitations/', 
         PlanInvitationCreateView.as_view(), 
         name='plan-invitation-list-create'),
    
    # Create bulk invitations (multiple members at once)
    path('plans/invitations/bulk/', 
         BulkPlanInvitationCreateView.as_view(), 
         name='plan-invitation-bulk-create'),

    # List invitations for a plan
    path('plans/<str:plan_type>/<int:plan_id>/invitations/', 
         PlanInvitationListView.as_view(), 
         name='plan-invitations-list'),
    
    # Accept/decline invitation
    path('invitations/respond/', 
         PlanInvitationResponseView.as_view(), 
         name='plan-invitation-respond'),

    path('', include(router.urls)),

]
