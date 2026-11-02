from rest_framework import serializers

from apps.qualification_test.models.exam import QuestionCategory, DifficultyLevel, Question


class QuestionCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionCategory
        fields = '__all__'


class DifficultyLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = DifficultyLevel
        fields = '__all__'


class QuestionSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source="category.name", read_only=True)
    difficulty = serializers.CharField(source="difficulty.name", read_only=True)

    class Meta:
        model = Question
        fields = ["id", "source_text", "question_body", "options", "question_type", "category",
                  "difficulty"]
