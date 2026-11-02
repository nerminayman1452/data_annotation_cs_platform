from django.db.models import Count
from django.utils.timezone import now
from django.db import models, transaction

from apps.image_annotation.models.task_img_object_detection import ObjectDetectionTask, ObjectDetectionAnnotation, \
    ObjectDetectionStatusHistory
from apps.image_annotation.models.task_img_polygons import PolygonTask, PolygonAnnotation, PolygonStatusHistory
from apps.project_management.models.plan_members import PlanMember
from apps.image_annotation.models.task_img_classification import (
    ImageClassificationTask,
    ImageClassificationAnnotation,
    ImageClassificationStatusHistory,
)
from apps.text_annotation.models import TextPlanTask
from apps.text_annotation.models.task_annotation import TextTaskAnnotation


class TaskAssigner:
    """
    Assigns tasks in batches and safely promotes one annotation at a time.
    """
    def __init__(self, plan):
        self.plan = plan
        self.config = plan.plan_config
        self.max_tasks_per_annotator = self.config.max_tasks_per_annotator
        self.target_annotators_per_task = self.config.annotators_per_task
        self.is_auto = self.config.task_distribution_mode == "auto"

        self._set_models()
        self.max_tasks_per_plan = self.TaskModel.objects.filter(plan=self.plan).count()


    def _set_models(self):
        """Set the models based on Image annotation type."""
        if self.annotation_type == "classification":
            self.TaskModel = ImageClassificationTask
            self.AnnotationModel = ImageClassificationAnnotation
            self.StatusHistoryModel = ImageClassificationStatusHistory

        elif self.annotation_type == "polygon":
            self.TaskModel = PolygonTask
            self.AnnotationModel = PolygonAnnotation
            self.StatusHistoryModel = PolygonStatusHistory

        elif self.annotation_type == "object_detection":
            self.TaskModel = ObjectDetectionTask
            self.AnnotationModel = ObjectDetectionAnnotation
            self.StatusHistoryModel = ObjectDetectionStatusHistory

        else:
            raise ValueError(f"Unsupported annotation type: {self.annotation_type}")

    def assign_initial_tasks(self):
        """Initial bulk assignment of tasks to all available annotators in batch (auto/manual)."""
        annotators = PlanMember.objects.filter(batch=self.batch)
        tasks = self.TaskModel.objects.filter(plan=self.plan)

        for task in tasks:
            if self._has_enough_annotators(task):
                continue

            for annotator in annotators:
                if self._has_max_tasks_active(annotator) or self._already_assigned(task, annotator):
                    continue

                self._assign_task(task, annotator)

                if self._has_enough_annotators(task):
                    break

    def auto_assign_next_tasks(self, annotator):
        """Assign next task if the user has no active tasks (works for new users too)."""
        if not self.is_auto:
            return None  # Skip auto-assign if disabled

        if self._has_completed_current_tasks(annotator) or not self._has_active_tasks(annotator):
            return self._assign_next_available_tasks(annotator)
        else:
            return None

    def manual_assign_next_tasks(self, annotator):
        """Manually triggered assignment of next task batch (manual mode)."""
        if self.is_auto:
            return None  # Skip manual logic if auto enabled

        return self._assign_next_available_tasks(annotator)

    def _has_max_tasks_active(self, annotator):
        """
        Do not allocate more if user already holds up to max assigned or in_progress.
        """
        task_count = self.AnnotationModel.objects.filter(
            annotator=annotator,
            task__plan=self.plan,
            status__in=["assigned", "in_progress"]
        ).count()
        return task_count >= self.max_tasks_per_annotator

    def _has_enough_annotators(self, task):
        return self.AnnotationModel.objects.filter(task=task).count() >= self.target_annotators_per_task

    def _already_assigned(self, task, annotator):
        return self.AnnotationModel.objects.filter(task=task, annotator=annotator).exists()

    def _has_completed_current_tasks(self, annotator):
        # Get the number of completed tasks by the annotator in this plan

        membership = PlanMember.objects.filter(profile=annotator.profile, plan=self.plan).first()
        if membership:
            completed_task_count = self.AnnotationModel.objects.filter(
                annotator=annotator,
                task__plan=self.plan,
                status='submitted'
            ).count()
            # If the annotator hasn't finished a full assigned tasks yet (e.g. 10), don't assign new ones
            return completed_task_count >= self.max_tasks_per_annotator
        return False

    def _has_active_tasks(self, annotator):
        active_count = self.AnnotationModel.objects.filter(
            annotator=annotator,
            task__plan=self.plan,
            status__in=['assigned', 'in_progress']
        ).count()
        return active_count >= self.max_tasks_per_annotator

    def _assign_task(self, task, annotator):
        annotation = self.AnnotationModel.objects.create(
            task=task,
            annotator=annotator,
            status="assigned",
            created_at=now(),
            updated_at=now(),
        )
        self.StatusHistoryModel.objects.create(
            annotation=annotation,
            status="assigned",
            started_at=now(),
        )
        return annotation

    def _assign_next_available_tasks(self, annotator):

        # Only assign a new tasks if:
        # - The annotator has finished previous allowed tasks
        # - AND has no active tasks (or fewer than allowed)
        if self._has_active_tasks(annotator):
            print("No tasks assigned: conditions not met.")
            return []

        # if not self._has_completed_current_tasks(annotator):
        #     print("No tasks assigned: annotator has not completed current tasks.")
        #     return []

        available_tasks = self.TaskModel.objects.filter(plan=self.plan).annotate(
            assigned_count=models.Count('annotations')
        ).filter(
            assigned_count__lt=self.target_annotators_per_task
        ).exclude(
            annotations__annotator=annotator
        )
        print("Available tasks for assignment:", available_tasks)

        # Take only up to max_tasks_per_annotator
        # tasks_to_assign = available_tasks[:self.max_tasks_per_plan]
        tasks_to_assign = available_tasks[:self.max_tasks_per_plan]
        print("Tasks to assign:", tasks_to_assign)

        assigned_tasks = []
        for task in tasks_to_assign:
            assigned = self._assign_task(task, annotator)
            if assigned:
                assigned_tasks.append(assigned)

        print("Assigned tasks:", assigned_tasks)

        return assigned_tasks

