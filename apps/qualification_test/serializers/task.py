from rest_framework import serializers

from apps.qualification_test.models.exam import ExamTask
from apps.qualification_test.serializers.question import QuestionSerializer


class ExamTaskSerializer(serializers.ModelSerializer):
    question = QuestionSerializer(read_only=True)
    annotator = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = ExamTask
        fields = [
            'id',
            'annotator',
            'question',
            'answer',
            "time_spent",
            # "changes",
            "status",
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'annotator', 'status']

    def validate_annotation_sentence(self, value):
        required_fields = ["answer"]
        for field in required_fields:
            if field not in value or value[field] in [None, "", []]:
                raise serializers.ValidationError(f"Missing or empty required field: {field}")
        return value

    def validate(self, attrs):
        request = self.context.get("request")
        user_id = request.user.id

        try:
            user_profile = Profile.objects.get(user_id=user_id)
        except Profile.DoesNotExist:
            raise serializers.ValidationError("Profile not found for current user.")

        instance = getattr(self, "instance", None)
        if instance:
            if instance.annotator.profile != user_profile:
                raise serializers.ValidationError(
                    "You cannot update another annotator's exam question."
                )
        if instance.status not in ["ASSIGNED", "SUBMITTED"]:
            raise serializers.ValidationError(
                f"Cannot update exam question when status is {instance.status}."
            )
        return attrs

    def update(self, instance, validated_data):
        """
        When answer is submitted, mark status as SUBMITTED.
        """
        answer = validated_data.get("answer", None)

        if instance.status == "ASSIGNED" and answer:
            validated_data["status"] = "SUBMITTED"

        elif instance.status == "SUBMITTED" and answer:
            validated_data["status"] = "SUBMITTED"

        return super().update(instance, validated_data)
