import math
import random

from apps.qualification_test.models.exam import Question


class ExamPreparation:
    DEFAULT_DIFFICULTY = {"Easy": 20, "Medium": 60, "Hard": 20}

    def _normalize_distribution(self, data):
        """Convert 0–100% or raw values to normalized fractions summing to 1.0."""
        total = sum(data.values())
        if total == 0:
            raise ValueError("Distribution values cannot all be zero.")
        normalized = {k: round(v / total, 3) for k, v in data.items()}
        return normalized

    def _validate_distribution(self, category, difficulty, question_type):
        if (not math.isclose(sum(category.values()), 1.0) or
                not math.isclose(sum(difficulty.values()), 1.0) or
                not math.isclose(sum(question_type.values()), 1.0)):
            raise ValueError("Percentages in distributions must sum to 1.0")

    def _calculate_exam_blueprint(self, total_questions, category, difficulty, question_type):
        """Calculates the exact number of questions for each subgroup."""
        quotas = {}
        for category_name, category_pct in category.items():
            for difficulty_name, difficulty_pct in difficulty.items():
                for type_name, type_pct in question_type.items():
                    key = (category_name, difficulty_name, type_name)
                    quotas[key] = total_questions * category_pct * difficulty_pct * type_pct

        blueprint = {k: math.floor(v) for k, v in quotas.items()}

        remaining_questions = total_questions - sum(blueprint.values())

        # Distribute the remaining questions for group with the largest fractional remainders.
        if remaining_questions > 0:
            remainders = {k: quotas[k] - blueprint[k] for k in quotas}

            sorted_by_remainder = sorted(
                remainders.items(),
                key=lambda item: (-item[1], -quotas[item[0]])
            )

            # Assign the remaining questions to the top N groups.
            for i in range(remaining_questions):
                group_to_increment = sorted_by_remainder[i][0]
                blueprint[group_to_increment] += 1

        assert sum(blueprint.values()) == total_questions

        return blueprint

    def _get_random_distribution_from_db(self, field_name):
        """
        Return a random distribution 'category' or 'question_type'
        """
        values = list(
            Question.objects.values_list(field_name, flat=True)
            .distinct()
            .exclude(**{f"{field_name}__isnull": True})
        )
        if not values:
            raise ValueError(f"No available {field_name} found in database.")
        pct = round(1 / len(values), 3)
        return {v: pct for v in values}

    def _fetch_questions(self, exam_list, annotation_type):
        final_exam_questions = []
        used_question_ids = set()
        for (category_name, difficulty_name, question_type), count in exam_list.items():
            if count <= 0:
                continue

            questions = Question.objects.filter(
                annotation_type=annotation_type,
                category__name=category_name,
                difficulty__name=difficulty_name,
                question_type=question_type,
            ).exclude(id__in=used_question_ids).order_by('?')

            selected_questions = list(questions[:count])

            if len(selected_questions) < count:
                raise ValueError(
                    f"Not enough questions in bank for '{category_name}/{difficulty_name}/{question_type}'. "
                    f"Required: {count}, Found: {len(selected_questions)}"
                )

            final_exam_questions.extend(selected_questions)
            used_question_ids.update(q.id for q in selected_questions)

        random.shuffle(final_exam_questions)
        return final_exam_questions

    def generate_exam(self, total_questions, category, difficulty, question_type, annotation_type):
        if not category:
            print("Category not provided — randomizing from DB.")
            category = self._get_random_distribution_from_db("category__name")

        if not difficulty:
            print("Difficulty not provided — using default distribution.")
            difficulty = self.DEFAULT_DIFFICULTY.copy()

        if not question_type:
            print("Question type not provided — randomizing from DB.")
            question_type = self._get_random_distribution_from_db("question_type")

        category = self._normalize_distribution(category)
        difficulty = self._normalize_distribution(difficulty)
        question_type = self._normalize_distribution(question_type)
        self._validate_distribution(category, difficulty, question_type)

        exam_blueprint = self._calculate_exam_blueprint(total_questions, category, difficulty, question_type)

        questions = self._fetch_questions(exam_blueprint, annotation_type)

        return questions
