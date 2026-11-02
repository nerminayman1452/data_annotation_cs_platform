from django.db import transaction
import random
from apps.project_management.models.plan_members import PlanMember
from apps.project_management.models.batch import Batch
from apps.project_management.models.text_plan import TextPlanRawData
# from apps.text_annotation.models.plan_text_labelling import TextLabellingPlan, PlanLabellingConfig
from apps.text_annotation.models.task_text_labelling import TextLabellingTaskResult


def generate_text_labeling_tasks(batch_id: int, plan_id: int):
    """
    Generate text labeling tasks for all annotators in the batch
    """
    plan = TextLabellingPlan.objects.filter(id=plan_id).first()
    batch = Batch.objects.get(id=batch_id)

    #todo take from segmented data table instead
    batch_data_list = TextPlanRawData.objects.filter(batch=batch_id)
    annotators = PlanMember.objects.filter(batch=batch_id, user_role='Annotator')

    plan_labelling_config = PlanLabellingConfig.objects.filter(id=plan.plan_labelling_conf_id.id).first()
    maximum_annotators = plan_labelling_config.annotators_per_task
    task_instances = []

    # Wrap in transaction for atomicity, used to maintain data integrity
    with transaction.atomic():
        # Iterate through all the batch data items - segmented data later
        for data_item in batch_data_list:
            # Randomly shuffle the annotators and select the required number
            selected_annotators = random.sample(list(annotators), min(maximum_annotators, len(annotators)))

            for annotator in selected_annotators:
                existing_task = TextLabellingTaskResult.objects.filter(
                    annotator=annotator,
                    batch=batch,
                    batch_data=data_item,
                    plan_labelling=plan.id
                ).first()

                if not existing_task:
                    task = TextLabellingTaskResult(
                        batch_data=data_item,
                        batch=batch,
                        plan_labelling=plan,
                        annotator=annotator,
                        status="in_progress"
                    )
                    task_instances.append(task)

        # Create all tasks in bulk to optimize database writes
        created_tasks = TextLabellingTaskResult.objects.bulk_create(task_instances)

    return created_tasks
