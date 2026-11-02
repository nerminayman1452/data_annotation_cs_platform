from django.contrib import admin

from apps.text_annotation.models import TextPlanTask
from apps.text_annotation.models.locations import Locations

# TextValidationType, \
from apps.text_annotation.models.qualification_config import QualificationConfig, QualificationTest, WorkerQualification
# from apps.text_annotation.models.review_text_labelling import ReviewTextLabellingResult
# from apps.text_annotation.models.review_text_segmentation import ReviewTextSegmentationResult
# from apps.text_annotation.models.review_text_summarization import ReviewTextSummarizationResult
# from apps.text_annotation.models.review_text_validation import ReviewTextValidationResult

# from apps.text_annotation.models.task_text_labelling import TextLabellingTaskResult
# from apps.text_annotation.models.task_text_segmentation import TextSegmentationTaskResult
# from apps.text_annotation.models.task_text_summarization import TextSummarizationTaskResult
# from apps.text_annotation.models.task_text_validation import TextValidationTaskResult

#labelling models
# admin.site.register(TextSentenceType)
# admin.site.register(TextLabelType)
# admin.site.register(TextErrorType)
# admin.site.register(PlanLabellingConfig)
# admin.site.register(TextLabellingPlan)

#Validation models
# admin.site.register(TextValidationType)
# admin.site.register(PlanValidationConfig)
# admin.site.register(TextValidationPlan)

#Segmentation models
# admin.site.register(TextSplitter)
# admin.site.register(TextSegmentationPlan)

#summarization models
# admin.site.register(PlanSummarizationConfig)
# admin.site.register(TextSummarizationPlan)

#annotation tasks
# admin.site.register(TextLabellingTaskResult)
# admin.site.register(TextValidationTaskResult)
# admin.site.register(TextSummarizationTaskResult)
# admin.site.register(TextSegmentationTaskResult)

# review results
# admin.site.register(ReviewTextLabellingResult)
# admin.site.register(ReviewTextValidationResult)
# admin.site.register(ReviewTextSegmentationResult)
# admin.site.register(ReviewTextSummarizationResult)

#qualifications
# admin.site.register(Locations)
# admin.site.register(QualificationConfig)
# admin.site.register(QualificationTest)
# admin.site.register(WorkerQualification)



admin.site.register(TextPlanTask)



