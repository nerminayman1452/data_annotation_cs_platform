from rest_framework.exceptions import PermissionDenied

from apps.project_management.models.plan_members import PlanMember
from apps.qualification_test.models.exam import ExamTask, ExamTaskReview


class ExamTaskReviewService:
    """
    Service to handle manual assignment and submission of annotator tasks to reviewers.
    """

    @staticmethod
    def get_tasks_ready_to_assign(annotator_exam_member, batch):
        """
        Returns all exam tasks for a given annotator and batch that can be assigned to a reviewer.
        """
        return ExamTask.objects.filter(
            annotator=annotator_exam_member,
            exam=batch.exam,
            status__in=["REVIEWER_PENDING"]
        )

    @staticmethod
    def _validate_reviewer(reviewer, batch):
        """
        Ensure the reviewer is authorized (batch owner or a reviewer/super-reviewer).
        """
        if reviewer == batch.owner:
            return True

        is_reviewer = PlanMember.objects.filter(
            batch=batch,
            profile=reviewer,
            role__in=["REVIEWER", "SUPER_REVIEWER"]
        ).exists()

        if not is_reviewer:
            raise PermissionDenied("The selected reviewer is not part of this batch.")
        return True

    @classmethod
    def assign_reviewer_to_annotator_tasks(cls, annotator_exam_member, reviewer, batch):
        """
        Assigns all exam tasks for the given annotator to the given reviewer.
        """
        cls._validate_reviewer(reviewer, batch)

        tasks = cls.get_tasks_ready_to_assign(annotator_exam_member, batch).select_related("exam", "annotator")

        assigned = []
        for task in tasks:
            review, created = ExamTaskReview.objects.get_or_create(
                task=task,
                reviewer=reviewer,
                defaults={"feedback": "", "decision": "PENDING"}
            )
            if created:
                task.status = "UNDER_REVIEW"
                task.save(update_fields=["status"])
                assigned.append(review)
        return assigned
