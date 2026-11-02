from django.urls import path

# from apps.image_annotation.views.annotation_image import NextTaskView, SubmitAnnotationView, \
#     AnnotatorProgressAPIView, SkipImageClassificationTaskAPIView, ActiveAssignedTasks
# from apps.image_annotation.views.annotation_task_assignment import AssignTasksAPIView
# from apps.image_annotation.views.batch_task import ImageBatchTasksAPIView
# from apps.image_annotation.views.batch import ImageLabelTypeView, ImageBatchView, \
#     ImageBatchDetailsView
# from apps.image_annotation.views.plan_img_object_detection import ObjectDetectionPlanView, ObjectDetectionLabelTypeView, \
#     ObjectDetectionPlanDetailsView
# from apps.image_annotation.views.plan_img_polygons import PolygonSegmentationPlanView, ImagePolygonLabelTypeView, \
#     PolygonSegmentationPlanDetailsView
from apps.tasks.views.task_generator import GeneratePlanTasksAPIView
# from apps.image_annotation.views.task_img_classification import ImageClassificationTasksAPIView, \
#     AssignImageClassificationTasksAPIView
# from apps.image_annotation.views.task_img_object_detection import ImageObjectDetectionTasksAPIView
# from apps.image_annotation.views.task_img_polygons import ImagePolygonTasksAPIView

urlpatterns = [
    # path('create/image-label-type/', ImageLabelTypeView.as_view(), name='create-image-label-type'),
    # path('create/image-object-detection-label-type/', ObjectDetectionLabelTypeView.as_view(), name='create-object-detection-label-type'),
    # path('create/image-polygon-label-type/', ImagePolygonLabelTypeView.as_view(), name='create-image-polygon-label-type'),

    # path('create/image-batch/<int:project_id>/', ImageBatchView.as_view(), name='create-image-batch'),
    # path('image-batch/<int:project_id>/', ImageBatchView.as_view(), name='list-image-batches'),
    # path('image-batch/<int:project_id>/<int:batch_id>/', ImageBatchDetailsView.as_view(),
    #      name='image-batch-details'),
    #
    # path('create/image-object-detection-plan/<int:batch_id>/', ObjectDetectionPlanView.as_view(), name='create-image-object-detection-plan'),
    # path('image-object-detection-plans/<int:batch_id>/', ObjectDetectionPlanView.as_view(), name='list-image-object-detection-plans'),
    # path('image-object-detection-plans/<int:batch_id>/<int:plan_id>', ObjectDetectionPlanDetailsView.as_view(),
    #      name='object-detection-plan-details'),
    #
    # path('create/image-polygon-plan/<int:batch_id>/', PolygonSegmentationPlanView.as_view(), name='create-image-polygon-plan'),
    # path('image-polygon-plans/<int:batch_id>/', PolygonSegmentationPlanView.as_view(), name='list-image-polygon-plans'),
    # path('image-polygon-plans/<int:batch_id>/<int:plan_id>', PolygonSegmentationPlanDetailsView.as_view(),
    #      name='image-polygon-plan-details'),
    #
    # path('generate/image-task/', ImageBatchTasksAPIView.as_view(), name='generate-image-batch-task'),
    # path('image-tasks/<int:batch_id>/', ImageBatchTasksAPIView.as_view(), name='list-image-batch-tasks'),
    #
    # # path('generate/image-object-detection-task/', ImageObjectDetectionTasksAPIView.as_view(), name='generate-image-object-detection-task'),
    # # path('image-object-detection-tasks/<int:batch_id>/<int:plan_id>/', ImageObjectDetectionTasksAPIView.as_view(),name='list-image-object-detection-tasks'),
    #
    # # path('generate/image-polygon-task/', ImagePolygonTasksAPIView.as_view(), name='generate-image-polygon-task'),
    # # path('image-polygon-tasks/<int:batch_id>/<int:plan_id>/', ImagePolygonTasksAPIView.as_view(),name='list-image-polygon-tasks'),
    #
    #
    # #through the admin / or project owner
    # path('assign/image-tasks/<int:batch_id>/',AssignTasksAPIView.as_view(),name='autoassign-image-classification-tasks'),
    #
    # #through the annotator
    # path('image-classification-tasks/<int:batch_id>/next/',NextTaskView.as_view(), name='next-image-classification-task'),
    # path('image-classification-tasks/<int:batch_id>/active-assigned/',ActiveAssignedTasks.as_view(), name='active-assigned-tasks'),
    # path('image-annotations-tasks/submit/<int:annotation_id>/',SubmitAnnotationView.as_view(),name='submit-image-classification-annotation'),
    # path('image-annotations-tasks/<int:batch_id>/progress/',AnnotatorProgressAPIView.as_view(),name='get-image-annotations-tasks-progress'),
    # path('image-annotations-tasks/skip/<int:annotation_id>/',SkipImageClassificationTaskAPIView.as_view(),name='skip-image-classification-task'),
    path("plans/generate-tasks/", GeneratePlanTasksAPIView.as_view(), name="generate-plan-tasks"),


]
