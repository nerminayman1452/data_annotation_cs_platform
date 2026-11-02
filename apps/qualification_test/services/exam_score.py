from django.db import transaction

from apps.project_management.models.plan_members import PlanMember
from apps.qualification_test.models.exam import ExamTask

FINAL_STATES = [
    "CORRECT_EXAM_ANSWER",
    "WRONG_EXAM_ANSWER",
]

CORRECT_STATES = [
    "CORRECT_EXAM_ANSWER",
]


class ExamScoreService:
    """Handles the scoring logic for exam submissions."""

    @staticmethod
    def get_exam_tasks(exam_member):
        """Return all tasks belonging to an exam member."""
        return ExamTask.objects.filter(annotator=exam_member)

    @staticmethod
    def validate_tasks_completed(tasks):
        """Check whether all tasks are in a final state."""
        total = tasks.count()
        if total == 0:
            return (False, 0, 0)
        pending = tasks.exclude(status__in=FINAL_STATES).count()
        return (pending == 0, total, pending)

    @staticmethod
    def calculate_score_percentage(tasks):
        """Calculate percentage of correct answers."""
        total = tasks.count()
        if total == 0:
            return 0.0
        correct = tasks.filter(status__in=CORRECT_STATES).count()
        return round((correct / total) * 100, 2)

    @staticmethod
    def update_exam_member_score(exam_member, score):
        """Save calculated score and pass/fail result."""
        passing_score = getattr(exam_member.exam, "passing_score", 0)
        exam_member.score = score
        exam_member.is_passed = score >= passing_score
        exam_member.save(update_fields=["score", "is_passed"])
        return exam_member.is_passed

    @staticmethod
    def enroll_to_batch_if_passed(exam_member):
        """Enroll annotator to batch if exam passed."""
        if exam_member.is_passed and exam_member.plan:
            PlanMember.objects.get_or_create(
                batch=exam_member.plan,
                profile=exam_member.profile,
                defaults={'role': 'ANNOTATOR'}
            )

    @classmethod
    @transaction.atomic
    def calculate_final_score(cls, exam_member):
        """Main entry point: orchestrates the full evaluation."""
        tasks = cls.get_exam_tasks(exam_member)
        all_completed, total, pending = cls.validate_tasks_completed(tasks)

        if total == 0:
            return 0.0
        if not all_completed:
            return None  # still pending grading

        score = cls.calculate_score_percentage(tasks)
        passed = cls.update_exam_member_score(exam_member, score)
        if passed:
            cls.enroll_to_batch_if_passed(exam_member)
        print("score calculated")
        return score

