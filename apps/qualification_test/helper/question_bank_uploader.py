from apps.qualification_test.helper.file_parser import FileParser
from apps.qualification_test.models.exam import Question, QuestionCategory, DifficultyLevel


class QuestionBankUploader:
    def _determine_question_type(self, row, default_question_type):
        file_question_type = str(row.get("question_type", "")).strip().upper()

        if file_question_type:
            if file_question_type not in dict(Question.QuestionType.choices):
                raise ValueError(f"Invalid question_type in Excel: {file_question_type}")
            return file_question_type
        if default_question_type:
            return default_question_type
        raise ValueError("Question type is missing in both Excel and API input.")

    def _get_or_create_dependencies(self, category_name, difficulty_name):
        """(Internal) Ensures Category, Difficulty, and Type objects exist."""
        category, _ = QuestionCategory.objects.get_or_create(name=category_name)
        difficulty, _ = DifficultyLevel.objects.get_or_create(name=difficulty_name)
        return category, difficulty

    def add_questions_from_file(self, uploaded_file, annotation_type, default_question_type=None):
        try:

            parser = FileParser(uploaded_file)
            df = parser.parse()
        except Exception as e:
            raise ValueError(f"Could not parse the Excel file. Error: {e}")
        questions = []

        for _, row in df.iterrows():

            question_type = self._determine_question_type(row, default_question_type)
            # Normalize text fields
            source = str(row.get("source", "")).strip()
            target = str(row.get("mt", "")).strip()
            question_body = str(row.get("question_body", "")).strip()

            correct = str(row.get("model_answer", "")).strip()
            category_name = str(row.get("question_category", "")).strip().capitalize()
            difficulty_name = str(row.get("difficulty", "")).strip().capitalize()
            category, difficulty = self._get_or_create_dependencies(category_name, difficulty_name)
            options_dict = {}
            correct_dict = {}
            if correct:
                correct_dict["answer"] = correct
            if question_type in [Question.QuestionType.MCQ, Question.QuestionType.TRUE_FALSE]:
                options_data = str(row.get("options", "")).strip()
                if options_data:
                    options_dict['choices'] = [opt.strip() for opt in options_data.split(",")]
            question = Question(
                source_text=source,
                machine_translation=target,
                question_body=question_body,
                options=options_dict,
                correct_answer=correct_dict,
                category=category,
                difficulty=difficulty,
                question_type=question_type,
                annotation_type=annotation_type,
            )
            questions.append(question)
        if questions:
            Question.objects.bulk_create(questions, ignore_conflicts=True)
        print(f"Successfully imported {len(df)} questions")
