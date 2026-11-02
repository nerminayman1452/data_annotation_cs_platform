from django.urls import path

# from apps.text_annotation.views.labelling_types import TextLabelTypeView, TextErrorTypeView, TextSentenceTypeView
# from apps.text_annotation.views.plan_segmentation import TextSegmentationPlanAPIView
# from apps.text_annotation.views.task_segmentation_result import TextSegmentationTasksAPIView
# from apps.text_annotation.views.text_splitter import TextSplitterView
# from apps.text_annotation.views.plan_text_labelling import TextLabelPlanView
# from apps.text_annotation.views.plan_text_summarization import TextSummarizationPlanView
# from apps.text_annotation.views.plan_text_validation import TextValidationPlanView
# from apps.text_annotation.views.review_text_labelling import ReviewTextLabellingResultListCreateAPIView
# from apps.text_annotation.views.review_text_summarization import ReviewTextSummarizationResultListCreateAPIView
# from apps.text_annotation.views.review_text_validation import ReviewTextValidationResultListCreateAPIView
from apps.tasks.views.task_generator import GeneratePlanTasksAPIView
# from apps.text_annotation.views.task_segmentation_result import TextSegmentationTasksAPIView
# from apps.text_annotation.views.text_labelling_task import TextLabelingTasksAPIView
# from apps.text_annotation.views.text_splitter import TextSplitterView

# from apps.text_annotation.views.text_summarization_task import TextSummarizationTasksAPIView
# from apps.text_annotation.views.text_validation_task import TextValidationTasksAPIView
# from apps.text_annotation.views.validation_types import TextValidationTypeView

urlpatterns = [
#     path('create/text-label-type/', TextLabelTypeView.as_view(), name='create-text-label-type'),
#     path('create/text-sentence-type/', TextSentenceTypeView.as_view(), name='create-text-sentence-type'),
#     path('create/text-error-type/', TextErrorTypeView.as_view(), name='create-text-error-type'),
    #     path('create/text-validation-type/', TextValidationTypeView.as_view(), name='create-text-validation-type'),
#     path('create/text-segmentation-splitter/', TextSplitterView.as_view(), name='create-text-segmentation-splitter'),

#     path('create/text-label-plan/<int:batch_id>/', TextLabelPlanView.as_view(), name='create-text-labelling-plan'),
#     path('text-label-plans/<int:batch_id>/', TextLabelPlanView.as_view(), name='list-text-labelling-plans'),
    #     path('create/text-validation-plan/<int:batch_id>/', TextValidationPlanView.as_view(),
    #          name='create-text-validation-plan'),
    #     path('text-validation-plans/<int:batch_id>/', TextValidationPlanView.as_view(), name='list-text-validation-plans'),
#     path('create/text-summarization-plan/<int:batch_id>/', TextSummarizationPlanView.as_view(),
#          name='create-text-summarization-plan'),
#     path('text-summarization-plans/<int:batch_id>/', TextSummarizationPlanView.as_view(),
#          name='list-text-summarization-plans'),
#     path('text-segmentation-plans/<int:batch_id>/', TextSegmentationPlanAPIView.as_view(),
#          name='text-segmentation-plan'),
    #
    # # path('generate/text-label-task/', TextLabelingTasksAPIView.as_view(), name='generate-text-label-task'),
    # path('text-label-tasks/<int:batch_id>/<int:plan_id>/', TextLabelingTasksAPIView.as_view(),
    #      name='list-text-label-tasks'),
    # path('generate/text-validation-task/', TextValidationTasksAPIView.as_view(), name='generate-text-validation-task'),
    # path('text-validation-tasks/<int:batch_id>/<int:plan_id>/', TextValidationTasksAPIView.as_view(),
    #      name='list-text-validation-tasks'),
    # path('generate/text-summarization-task/', TextSummarizationTasksAPIView.as_view(),
    #      name='generate-text-summarization-task'),
    # path('text-summarization-tasks/<int:batch_id>/<int:plan_id>/', TextSummarizationTasksAPIView.as_view(),
    #      name='list-text-summarization-tasks'),

#     path('create/text-label-type/', TextSplitterView.as_view(), name='create-text-splitter'),

#     path('text-segmentation-tasks/<int:batch_id>/<int:plan_id>/', TextSegmentationTasksAPIView.as_view(),
#          name='segmentation-task-list-create'),
#     path('generate/text-validation-reviews/<int:plan_id>/', ReviewTextValidationResultListCreateAPIView.as_view(),
#          name='generate-text-summarization-reviews'
#          ),
#     path(
#         'text-validation-reviews/<int:plan_id>/',
#         ReviewTextValidationResultListCreateAPIView.as_view(),
#         name='review-text-validation-list-create'
#     ),
#     path(
#         'text-labelling-reviews/<int:plan_id>/',
#         ReviewTextLabellingResultListCreateAPIView.as_view(),
#         name='review-text-labelling-list-create'
#     ), path(
#         'text-summarization-reviews/<int:plan_id>/',
#         ReviewTextSummarizationResultListCreateAPIView.as_view(),
#         name='review-text-summarization-list-create'
#     ),



    path("plans/generate-tasks/", GeneratePlanTasksAPIView.as_view(), name="generate-plan-tasks"),

]
