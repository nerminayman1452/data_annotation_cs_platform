import re

from apps.qualification_test.models.exam import Question, ExamTask


# from difflib import SequenceMatcher


class ExamEvaluator:
    def __init__(self, threshold=0.8):
        self.threshold = threshold
        self.tasks_to_update = []

    def _extract_answer(self, answer_obj):
        if isinstance(answer_obj, dict):
            return str(answer_obj.get("answer", "")).strip().lower()
        return str(answer_obj).strip().lower()

    # def _normalize_arabic(self, text: str) -> str:
    #     """
    #     Normalizes Arabic text for fair comparison.
    #     - Removes diacritics (tashkeel).
    #     - Removes tatweel/kashida (ـ).
    #     """
    #     text = str(text)
    #     # Remove diacritics
    #     text = re.sub(r'[\u064B-\u0652]', '', text)
    #     # Remove tatweel
    #     text = re.sub(r'ـ', '', text)
    #     return text

    def _evaluate_mcq_or_tf(self, exam_task):
        """Grades an exact-match question (MCQ, T/F)."""
        user_answer = self._extract_answer(exam_task.answer)
        model_answer = self._extract_answer(exam_task.question.correct_answer)
        if not model_answer:
            exam_task.status = "REVIEWER_PENDING"
        elif user_answer == model_answer:
            exam_task.status = "CORRECT_EXAM_ANSWER"
        else:
            exam_task.status = "WRONG_EXAM_ANSWER"
        return exam_task

    # def check_similarity(self, answer, model_answer):
    #     normalized_answer = self._normalize_arabic(answer)
    #     normalized_model_answer = self._normalize_arabic(model_answer)
    #     if not normalized_answer or not normalized_model_answer:
    #         return 0.0
    #
    #     distance = Levenshtein.distance(normalized_answer, normalized_model_answer)
    #     max_len = max(len(normalized_answer), len(normalized_model_answer))
    #     similarity = (max_len - distance) / max_len
    #     return similarity

    def _evaluate_direct_edit(self, exam_task):
        """Evaluate a single sentence result after submission."""
        answer = self._extract_answer(exam_task.answer)
        model_answer = self._extract_answer(exam_task.question.correct_answer)
        # if not model_answer:
        exam_task.status = "REVIEWER_PENDING"
        # else:
        #     score = self.check_similarity(answer, model_answer)
        #     exam_task.status = (
        #         "CORRECT_EXAM_ANSWER" if score >= self.threshold else "REVIEWER_PENDING"
        #     )
        return exam_task

    def evaluate_question(self, question_type, exam_task):
        evaluators = {
            Question.QuestionType.MCQ: self._evaluate_mcq_or_tf,
            Question.QuestionType.TRUE_FALSE: self._evaluate_mcq_or_tf,
            Question.QuestionType.DIRECT_EDIT: self._evaluate_direct_edit,
        }
        evaluator = evaluators.get(question_type)
        return evaluator(exam_task)

    def evaluate_exam(self, exam_tasks):
        for task in exam_tasks:
            question_type = task.question.question_type
            self.tasks_to_update.append(self.evaluate_question(question_type, task))

        ExamTask.objects.bulk_update(self.tasks_to_update, ['status'])

    # @transaction.atomic
    # def calculate_exam_score(self, batch, annotator):
    #     annotations = ReviewAnnotation.objects.filter(
    #         sentence__batch=batch,
    #         annotator=annotator
    #     )
    #     total = annotations.count()
    #     if total == 0:
    #         return 0.0
    #     correct = annotations.filter(
    #         status__in=["CORRECT_EXAM_ANSWER", "REVIEWER_ACCEPTED"]
    #     ).count()
    #
    #     score_percent = round((correct / total) * 100, 2)
    #     ExamReviewBatchMembers.objects.filter(
    #         profile=annotator,
    #         batch=batch
    #     ).update(score=score_percent)
    #
    #     return score_percent
