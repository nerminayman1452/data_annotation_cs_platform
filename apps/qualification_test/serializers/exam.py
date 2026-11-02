import math

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.qualification_test.helper.question_bank_uploader import QuestionBankUploader
from apps.qualification_test.models.exam import Exam, Question, ExamBatchMembers


class ExamSerializer(serializers.ModelSerializer):
    owner_email = serializers.CharField(source='owner.email', read_only=True)
    owner_name = serializers.CharField(source='owner.__str__', read_only=True)

    class Meta:
        model = Exam
        fields = [
            'id',
            'name',
            'description',
            'owner',
            'owner_name',
            'owner_email',
            'total_questions',
            'duration',
            'category',
            'difficulty',
            'question_type',
            'annotation_type',
            'passing_score',
            'config',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at', 'owner']

    def validate_distribution_field(self, data, field_name):
        if not isinstance(data, dict):
            raise serializers.ValidationError({field_name: "Must be a JSON object."})

        normalized = {}
        total = sum(data.values())
        if total > 1.5:  # user probably entered 60 instead of 0.6
            normalized = {k: round(v / 100.0, 3) for k, v in data.items()}
        else:
            normalized = {k: round(v, 3) for k, v in data.items()}

        if not math.isclose(sum(normalized.values()), 1.0, rel_tol=1e-2):
            raise serializers.ValidationError({field_name: "Values must sum to 1.0"})

        return normalized

    def validate(self, data):
        # Optional: ensure valid JSON structures
        for field in ["category", "difficulty", "question_type"]:
            if field in data and not isinstance(data[field], dict):
                raise serializers.ValidationError({field: "Must be a valid JSON object."})
        return data


class QuestionBankUploadSerializer(serializers.Serializer):
    file = serializers.FileField(required=True)
    question_type = serializers.ChoiceField(choices=Question.QuestionType.choices, required=False, allow_null=True
                                            )
    # annotation_type = serializers.ChoiceField(choices=Exam.ANNOTATION_TYPES, required=True)

    def validate(self, attrs):
        file = attrs.get('file')
        if not file.name.endswith(('.xlsx', '.xls')):
            raise serializers.ValidationError("Only Excel files (.xlsx, .xls) are supported.")
        return attrs

    def create(self, validated_data):
        uploaded_file = validated_data['file']
        question_type = validated_data.get('question_type')
        annotation_type = validated_data['annotation_type']

        reader = QuestionBankUploader()
        reader.add_questions_from_file(uploaded_file, annotation_type, question_type)
        return {"annotation_type": annotation_type}


class ExamSubmissionSerializer(serializers.Serializer):
    """
    Serializer for submitting an exam.
    No input fields, only validation on the current user & exam.
    """

    def validate(self, attrs):
        request = self.context['request']
        exam_id = self.context.get('exam_id')
        user = request.user.id

        exam_member = ExamBatchMembers.objects.filter(
            profile__user_id=user,
            exam_id=exam_id,
            submitted=False
        ).select_related("exam", "profile").first()

        if not exam_member:
            raise ValidationError("No active exam attempt found for this exam or exam already submitted.")

        attrs['exam_member'] = exam_member
        return attrs
