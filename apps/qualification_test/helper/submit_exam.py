# apps/review/services/exam_submission_service.py

from django.db import transaction
from rest_framework.exceptions import ValidationError
from django_q.tasks import async_task

from apps.qualification_test.models.exam import ExamBatchMembers, ExamTask


class ExamSubmission:
    """Handles submission and automatic evaluation of annotator exam answers."""

    @staticmethod
    @transaction.atomic
    def submit_exam(annotator_exam_member_id):
        # Get the annotator’s exam member entry
        exam_member = (
            ExamBatchMembers.objects
            .select_related("exam", "batch", "profile")
            .filter(id=annotator_exam_member_id)
            .first()
        )

        if not exam_member:
            raise ValidationError("Exam membership not found.")
        if exam_member.submitted:
            raise ValidationError("This exam has already been submitted.")

        exam_member.submitted = True
        exam_member.save(update_fields=["submitted"])

        exam_tasks = ExamTask.objects.filter(annotator=exam_member)

        if not exam_tasks.exists():
            raise ValidationError("No tasks found for this exam member.")
        async_task(
            'apps.qualification_test.tasks.evaluate_exam.evaluate_exam_member_task',
            annotator_exam_member_id
        )
