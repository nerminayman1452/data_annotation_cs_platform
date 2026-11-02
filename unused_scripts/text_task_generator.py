# import random
# from django.db import transaction
#
# # from apps.project_management.models.segmented_batch_data import SegmentedBatchData
# from apps.text_annotation.services.file_reader import FileReader
#
#
# class BaseTaskGenerator:
#     def __init__(self, batch, plan, plan_config, annotators, model_refs):
#         self.batch = batch
#         self.plan = plan
#         self.plan_config = plan_config
#         self.annotators = annotators
#         self.model_refs = model_refs  # Dict with model references
#         self.task_instances = []
#
#     # def already_exists(self, **kwargs):
#     #     return self.model_refs.objects.filter(**kwargs).exists()
#     def build_batch_data_tasks(self, data_item, selected_annotators):
#         """
#         Store individual batch data content into tasks for annotation if there's no segmentation processes done.
#         """
#         content = FileReader.read(data_item.file.path if data_item.file else "")
#         for annotator in selected_annotators:
#             if not self.model_refs["task_model"].objects.filter(
#                 annotator=annotator,
#                 batch=self.batch,
#                 batch_data=data_item,
#                 plan=self.plan.id
#             ).exists():
#                 task = self.model_refs["task_model"](
#                     batch_data=data_item,
#                     batch=self.batch,
#                     plan=self.plan,
#                     annotator=annotator,
#                     data_content=content,
#                     status="in_progress"
#                 )
#                 self.task_instances.append(task)
#
#     def build_segmented_data_tasks(self, segments, selected_annotators, batch_data, segmented_data):
#         """
#         Store individual paragraph or sentence content into tasks for annotation.
#         """
#         key = "paragraphs" if self.plan.content_type == "Paragraph" else "sentences"
#         for part in segments.get(key, []):
#             text = part.get("paragraph") or part.get("sentence")
#             for annotator in selected_annotators:
#                 if not self.model_refs["task_model"].objects.filter(
#                     annotator=annotator,
#                     batch=self.batch,
#                     segmented_data=segmented_data,
#                     data_content=text,
#                     plan=self.plan
#                 ).exists():
#                     self.task_instances.append(
#                         self.model_refs["task_model"](
#                             segmented_data=segmented_data,
#                             data_content=text,
#                             batch=self.batch,
#                             batch_data=batch_data,
#                             plan=self.plan,
#                             annotator=annotator,
#                             status="in_progress"
#                         )
#                     )
#
#     def generate_tasks(self, batch_data_list):
#         """
#         Generate Annotation Tasks for all annotators in the batch
#         """
#         max_annotators = self.plan_config.annotators_per_task
#
#         with transaction.atomic():
#             for data_item in batch_data_list:
#                 selected_annotators = random.sample(list(self.annotators), min(max_annotators, len(self.annotators)))
#
#                 if self.plan.content_type == "Article":
#                     self.build_batch_data_tasks(data_item, selected_annotators)
#
#                 # elif self.plan.content_type in ["Paragraph", "Sentence"]:
#                 #     if data_item.content_type in ['paragraph', 'sentence']:
#                 #         self.build_batch_data_tasks(data_item, selected_annotators)
#                 #     else:
#                 #         segmented_data = SegmentedBatchData.objects.filter(batch_data=data_item.id).first()
#                 #         if not segmented_data:
#                 #             continue
#                 #         segments = segmented_data.paragraphs if self.plan.content_type == "Paragraph" else segmented_data.sentences
#                 #         if not segments:
#                 #             continue
#                 #         self.build_segmented_data_tasks(segments, selected_annotators, data_item, segmented_data)
#
#             return self.model_refs["task_model"].objects.bulk_create(self.task_instances)
from django.db import transaction

from apps.project_management.models import TextPlan
from apps.tasks.helpers.task_processor import ProcessorFactory
from apps.text_annotation.models import TextPlanTask


class TaskGenerationService:
    """
    Service responsible for populating the TextPlanTask table.
    """

    def generate_tasks(self, plan_id: int):
        try:
            plan = TextPlan.objects.select_related(
                'estimation_config__measure_unit'
            ).prefetch_related('raw_data_files').get(id=plan_id)
        except TextPlan.DoesNotExist:
            raise ValueError("Plan not found")

        measure_unit = "article"
        if plan.estimation_config and plan.estimation_config.measure_unit:
            measure_unit = plan.estimation_config.measure_unit.title

        # 🔥 ONE QUERY ONLY
        generated_files = set(
            TextPlanTask.objects.filter(plan=plan)
            .values_list("plan_file_id", flat=True)
            .distinct()
        )
        tasks_buffer = []

        # 3. Process each Raw File
        for raw_file in plan.raw_data_files.all():
            if raw_file.id in generated_files:
                continue
            file_path = raw_file.file.path

            # Get correct tools from Factory
            loader, strategy = ProcessorFactory.get_components(file_path, measure_unit)

            print(f"Processing {raw_file.file_name} as {measure_unit}...")

            try:
                # Load & Segment
                content = loader.load(file_path)

                for payload in strategy.segment(content):
                    # Create the Task Instance (In Memory)
                    task = TextPlanTask(
                        plan=plan,
                        plan_file=raw_file,
                        source_data=payload,  # Saves as JSON {"text": "..."} or {"col": "..."}
                        finalized_result=None,
                        # If you have an 'order' field in BasePlanTask, use payload.order
                    )
                    tasks_buffer.append(task)

            except Exception as e:
                print(f"Failed to process {raw_file.file_name}: {e}")
                # Log error to Sentry or DB log here

        # 4. Bulk Write to DB
        if tasks_buffer:
            with transaction.atomic():
                # batch_size=500 prevents memory overflow on massive imports
                TextPlanTask.objects.bulk_create(tasks_buffer, batch_size=500)

        return len(tasks_buffer)
