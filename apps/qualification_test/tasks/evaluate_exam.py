
from django_q.tasks import logger

from apps.qualification_test.models.exam import ExamBatchMembers, ExamTask
from apps.qualification_test.services.exam_evaluator import ExamEvaluator
from apps.qualification_test.services.exam_score import ExamScoreService


def evaluate_exam_member_task(exam_member_id):
    try:
        exam_member = ExamBatchMembers.objects.select_related(
            "exam", "batch", "profile"
        ).get(id=exam_member_id)
    except ExamBatchMembers.DoesNotExist:
        logger.error(f"ExamReviewBatchMembers with id {exam_member_id} not found.")
        return

    exam_tasks = ExamTask.objects.filter(annotator=exam_member).select_related("question")
    if not exam_tasks.exists():
        logger.warn(f"No exam tasks found for submission {exam_member_id}.")
        return
    evaluator = ExamEvaluator(threshold=0.9)
    evaluator.evaluate_exam(exam_tasks)
    print("evaluation finished")
    score = ExamScoreService()
    score.calculate_final_score(exam_member=exam_member)
