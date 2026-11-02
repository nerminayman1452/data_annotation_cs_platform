from django.db import transaction, IntegrityError
from django.db.models import Count, Q

from apps.project_management.models import PlanMember


# Import your models here
# from .models import ImagePlanTask, ImageTaskAnnotation, PlanMember

class TaskAssigner:
    """
    Assigns tasks in batches using the merged TaskAnnotation model.
    """
    ACTIVE_STATUSES = ["ASSIGNED", "IN_PROGRESS"]
    FINAL_STATUSES = ["SUBMITTED"]

    def __init__(self, plan):
        self.plan = plan
        self.config = plan.get_config()
        # Configuration limits
        self.tasks_per_worker = self.config.standard
        self.workers_per_task = self.config.workers_per_task
        self.is_auto = self.config.task_distribution_mode == "auto"
        self.TaskModel = plan.get_task_model()
        self.AnnotationTaskModel = plan.get_annotation_model()
        # Total tasks available in this specific plan
        # self.total_tasks_count = self.TaskModel.objects.filter(plan=self.plan).count()

    def assign_initial_tasks(self):
        """
        Initial bulk assignment to all available PlanMembers in the batch.
        """
        annotators = PlanMember.objects.filter(plan=self.plan)
        all_assignments = []
        for annotator in annotators:
            assigned = self._assign_available_tasks(annotator)
            all_assignments.extend(assigned)
        return all_assignments

    def auto_assign_next_tasks(self, member):
        if not self.is_auto:
            return []
        return self._assign_available_tasks(member)

    def manual_assign_next_tasks(self, member):
        if self.is_auto:
            return []
        return self._assign_available_tasks(member)

    def _get_available_tasks(self, member, limit):
        return (
            self.TaskModel.objects
            .filter(plan=self.plan)
            .annotate(
                assigned_count=Count("annotations"),
                is_member_assigned=Count(
                    "annotations",
                    filter=Q(annotations__member=member)
                )
            )
            .filter(
                assigned_count__lt=self.workers_per_task,
                is_member_assigned=0
            ).select_for_update(skip_locked=True)
            .order_by("-assigned_count", "id")[:limit]
        )

    def _has_active_tasks(self, member):
        return self.AnnotationTaskModel.objects.filter(
            member=member,
            plan_task__plan=self.plan,
            status__in=self.ACTIVE_STATUSES
        ).exists()

    def _assign_available_tasks(self, member):

        if self._has_active_tasks(member):
            return []
        slots = self._get_worker_quota(member)
        assignments = []
        with transaction.atomic():
            tasks = self._get_available_tasks(member, slots)
            for task in tasks:
                if task.annotations.count() >= self.workers_per_task:
                    continue
                assignment = self._assign_task(task, member)
                if assignment:
                    assignments.append(assignment)
        return assignments

    def _get_worker_quota(self, member):
        weight = getattr(member.profile, 'weight', 1.0)
        return max(1, int(self.tasks_per_worker * weight))
        # return min(quota, remaining_tasks)

    def _assign_task(self, task, member):
        try:
            return self.AnnotationTaskModel.objects.create(
                plan_task=task,
                member=member,
                status="ASSIGNED"
            )
        except IntegrityError:
            return None


    # def _has_completed_all_tasks(self, member):
    #     counts = self.AnnotationTaskModel.objects.filter(
    #         member=member,
    #         plan_task__plan=self.plan
    #     ).aggregate(
    #         total_assigned=Count("id"),
    #         total_completed=Count("id", filter=Q(status__in=self.FINAL_STATUSES))
    #     )
    #
    #     return counts["total_assigned"] == counts["total_completed"]

