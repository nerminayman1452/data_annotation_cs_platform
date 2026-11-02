from django.db import transaction

from apps.qualification_test.models.exam import ExamTask
from apps.qualification_test.services.question_distribution import ExamPreparation


class ExamAssignment:
    def __init__(self):
        self.blueprint_generator = ExamPreparation()

    @transaction.atomic
    def assign_exam_to_annotator(self, annotator_profile, exam):
        total_questions = exam.total_questions
        category = exam.category
        difficulty = exam.difficulty
        question_type = exam.question_type
        annotation_type = exam.annotation_type
        questions = self.blueprint_generator.generate_exam(total_questions, category, difficulty, question_type, annotation_type)
        if ExamTask.objects.filter(annotator=annotator_profile, exam=exam).exists():
            raise ValueError("Exam tasks already assigned to this annotator.")
        exam_tasks = []
        for question in questions:
            exam_tasks.append(
                ExamTask(
                    exam=exam,
                    annotator=annotator_profile,
                    question=question,
                    status="ASSIGNED",
                )
            )

        ExamTask.objects.bulk_create(exam_tasks)
        return exam_tasks
