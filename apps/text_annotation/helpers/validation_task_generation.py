from django.db import transaction
import random
from apps.project_management.models.plan_members import PlanMember
from apps.project_management.models.batch import Batch
from apps.project_management.models.text_plan import TextPlanRawData
# from apps.text_annotation.models.plan_text_validation import TextValidationPlan, PlanValidationConfig
from apps.text_annotation.models.task_text_validation import TextValidationTaskResult


def generate_text_validation_tasks(batch_id: int, plan_id: int):
    """
    Generate text Validation tasks for all annotators in the batch
    """
    plan = TextValidationPlan.objects.filter(id=plan_id).first()
    batch = Batch.objects.get(id=batch_id)

    batch_data_list = TextPlanRawData.objects.filter(batch=batch_id)
    annotators = PlanMember.objects.filter(batch=batch_id, user_role='Annotator')

    plan_validation_config = PlanValidationConfig.objects.filter(id=plan.plan_validation_conf_id.id).first()
    maximum_annotators = plan_validation_config.annotators_per_task
    task_instances = []

    with transaction.atomic():
        for data_item in batch_data_list:
            selected_annotators = random.sample(list(annotators), min(maximum_annotators, len(annotators)))

            for annotator in selected_annotators:
                existing_task = TextValidationTaskResult.objects.filter(
                    annotator=annotator,
                    batch=batch,
                    batch_data=data_item,
                    plan_validation=plan.id
                ).first()

                if not existing_task:
                    task = TextValidationTaskResult(
                        batch_data=data_item,
                        batch=batch,
                        plan_validation=plan,
                        annotator=annotator,
                        status="in_progress"
                    )
                    task_instances.append(task)

        created_tasks = TextValidationTaskResult.objects.bulk_create(task_instances)

    return created_tasks
