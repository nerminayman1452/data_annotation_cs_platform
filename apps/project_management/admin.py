from django.contrib import admin

from apps.project_management.models import AudioPlan
from apps.project_management.models.annotation_type import AnnotationType
from apps.project_management.models.audio_plan import AudioPlanRawData, AudioPlanCostConfig, AudioPlanEstimationConfig, \
    AudioPlanConfig, AudioPlanStatusHistory, EmotionLabel, SpeakerLabel
from apps.project_management.models.batch import Batch, BatchStatusHistory
from apps.project_management.models.image_plan import ImagePlan, ImageLabelType, ImagePlanConfig, \
    ImagePlanCostConfig, ImagePlanEstimationConfig, ImagePlanStatusHistory, DetectionLabelType, PolygonLabelType
from apps.project_management.models.image_plan import ImagePlanRawData
from apps.project_management.models.organization import Organization
from apps.project_management.models.plan_members import PlanMember
from apps.project_management.models.project import Project
from apps.project_management.models.text_plan import TextPlan, TextPlanConfig, TextPlanCostConfig, \
    TextPlanEstimationConfig, TextSentenceType, TextLabelType, TextErrorType, TextValidationType, TextPlanStatusHistory
from apps.project_management.models.text_plan import TextPlanRawData
from apps.project_management.models.invitation import PlanInvitation

# from apps.project_management.models.segmented_batch_data import SegmentedBatchData


admin.site.register(AnnotationType)
admin.site.register(Organization)
admin.site.register(Project)
admin.site.register(Batch)
admin.site.register(BatchStatusHistory)
admin.site.register(PlanMember)

###IMAGE###
admin.site.register(ImagePlan)
admin.site.register(ImagePlanStatusHistory)
admin.site.register(ImagePlanRawData)
admin.site.register(ImagePlanConfig)
admin.site.register(ImagePlanCostConfig)
admin.site.register(ImagePlanEstimationConfig)
admin.site.register(ImageLabelType)
admin.site.register(DetectionLabelType)
admin.site.register(PolygonLabelType)

###TEXT###
admin.site.register(TextPlan)
admin.site.register(TextPlanStatusHistory)
admin.site.register(TextPlanRawData)
admin.site.register(TextPlanConfig)
admin.site.register(TextPlanCostConfig)
admin.site.register(TextPlanEstimationConfig)
admin.site.register(TextSentenceType)
admin.site.register(TextLabelType)
admin.site.register(TextErrorType)
admin.site.register(TextValidationType)

###AUDIO###
admin.site.register(AudioPlan)
admin.site.register(AudioPlanStatusHistory)
admin.site.register(AudioPlanRawData)
admin.site.register(AudioPlanConfig)
admin.site.register(AudioPlanCostConfig)
admin.site.register(AudioPlanEstimationConfig)
admin.site.register(EmotionLabel)
admin.site.register(SpeakerLabel)


#PLAN INVITATION
admin.site.register(PlanInvitation)



# admin.site.register(SegmentedBatchData)
