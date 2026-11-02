from apps.audio_annotation.models.plan_audio_labelling import AudioLabellingPlan
from apps.audio_annotation.models.task_audio_labelling import AudioLabellingTaskResult
from apps.project_management.models.audio_plan import AudioPlan
from apps.project_management.models.audio_plan import AudioPlanRawData


class AudioTaskLabellingGeneration:
    def __init__(self, plan_id, batch_id,request):
        self.labelling_plan = AudioLabellingPlan.objects.filter(id=plan_id).first()
        self.batch = AudioPlan.objects.get(id=batch_id)
        self.segmented_batch_data = AudioPlanRawData.objects.filter(batch=self.batch, result__isnull=False)

    def generate_labelling_task(self):
        for batch_data in self.segmented_batch_data:
            AudioLabellingTaskResult.objects.create(
                batch=batch_data.batch,
                batch_data=batch_data,
                plan=self.labelling_plan,
                task_name=f"{self.labelling_plan.plan_name} - {batch_data.id}",
                annotator=None,  # unassigned
                parent_result=None,  # this is the parent
                result=[],
                status="in_progress"
            )