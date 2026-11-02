from django.db.models.signals import post_save
from django.dispatch import receiver
from django_q.tasks import async_task

from apps.qualification_test.models.exam import ExamTask
from apps.qualification_test.services.exam_score import ExamScoreService


@receiver(post_save, sender=ExamTask)
def auto_calculate_exam_score(sender, instance, **kwargs):
    """
    run score calculation asynchronously.
    """
    exam_member = instance.annotator
    tasks = ExamScoreService.get_exam_tasks(exam_member)
    all_completed, total, pending = ExamScoreService.validate_tasks_completed(tasks)

    if total > 0 and pending == 0:
        async_task(
            "apps.qualification_test.services.exam_score.ExamScoreService.calculate_final_score",
            exam_member
        )