# from apps.image_annotation.models.plan_img_classification import ImageClassificationPlan
from apps.image_annotation.models.plan_task import ImagePlanTask

# from apps.project_management.models.image_batch_data import ImageBatchData

#
# class ImageAnnotationTaskGenerator:
#     def __init__(self, plan):
#         self.plan = plan
#         self.batch = plan.batch
#
#     def generate_tasks(self):
#         """
#         Entry point for generating tasks based on plan type.
#         """
#         # if isinstance(self.plan, ImageClassificationPlan):
#         #     return self._generate_classification_tasks()
#
#         if isinstance(self.plan, ObjectDetectionPlan):
#             return self._generate_object_detection_tasks()
#
#         elif isinstance(self.plan, PolygonPlan):
#             return self._generate_polygon_segmentation_tasks()
#
#         else:
#             raise ValueError("Unsupported plan type for task generation.")
#
#     def _generate_classification_tasks(self):
#         """
#         Generate tasks for Image Classification.
#         One task per image.
#         """
#         tasks = []
#         #todo
#         #filter with also image annotations plans (img batch data)
#         # batch_data_items = ImageBatchData.objects.filter(batch=self.batch,plan_classification=self.plan)
#         #
#         # for data_item in batch_data_items:
#         #     task, created = ImageClassificationTask.objects.get_or_create(
#         #         batch=self.batch,
#         #         batch_data=data_item,
#         #         plan=self.plan,
#         #         # image_url = data_item.image_url ,
#         #         # defaults={"status": "pending"}
#         #     )
#         #     if created:
#         #         tasks.append(task)
#         # return tasks
#         pass
#
#     def _generate_object_detection_tasks(self):
#         """
#         Generate tasks for Object Detection.
#         One task per image.
#         """
#         tasks = []
#         # batch_data_items = ImageBatchData.objects.filter(batch=self.batch,plan_object_detection=self.plan)
#
#         # for data_item in batch_data_items:
#         #     task, created = ObjectDetectionTask.objects.get_or_create(
#         #         batch=self.batch,
#         #         batch_data=data_item,
#         #         plan=self.plan,
#         #         # image_url = data_item.image_url ,
#         #     )
#         #     if created:
#         #         tasks.append(task)
#         # return tasks
#         pass
#
#     def _generate_polygon_segmentation_tasks(self):
#         """
#         Generate tasks for Polygon Annotation.
#         One task per image.
#         """
#         tasks = []
#         # batch_data_items = ImageBatchData.objects.filter(batch=self.batch,plan_polygon=self.plan)
#
#         # for data_item in batch_data_items:
#         #     task, created = PolygonTask.objects.get_or_create(
#         #         batch=self.batch,
#         #         batch_data=data_item,
#         #         # image_url = data_item.image_url ,
#         #         plan=self.plan,
#         #     )
#         #     if created:
#         #         tasks.append(task)
#         # return tasks
#         pass

from apps.project_management.models import ImagePlanRawData


class ImageAnnotationTaskGenerator:
    def __init__(self, plan):
        self.plan = plan

    def generate_plan_tasks(self):
        """
        Converts raw uploaded files (ImagePlanRawData) into workable Tasks (ImageBatchTask).
        """
        existing_raw_file_ids = set(
            self.plan.plan_tasks.values_list('plan_file_id', flat=True)
        )

        raw_files_to_process = self.plan.raw_data_units.exclude(
            id__in=existing_raw_file_ids
        )
        new_tasks = []
        for raw_file in raw_files_to_process:
            data = {
                "file_url": raw_file.file.url if raw_file.file else "",
                # "metadata": raw_file.metadata
            }
            new_task = ImagePlanTask(
                plan=self.plan,
                plan_file=raw_file,
                source_data=data
            )
            new_tasks.append(new_task)
        # 3. Bulk Create
        if new_tasks:
            ImagePlanTask.objects.bulk_create(new_tasks)
        return len(new_tasks)
