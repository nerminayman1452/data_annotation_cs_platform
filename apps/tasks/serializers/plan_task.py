from rest_framework import serializers


class BasePlanTaskSerializer(serializers.ModelSerializer):
    accepted_by = serializers.StringRelatedField()

    class Meta:
        fields = [
            "id",
            "source_data",
            "finalized_result",
            "accepted_by",
            "accepted_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ['accepted_by', 'accepted_at', 'created_at', 'updated_at']
        
class GenerateTasksSerializer(serializers.Serializer):
    PLAN_TYPE_CHOICES = [
        ("text", "Text Plan"),
        ("image", "Image Plan"),
    ]

    plan_id = serializers.IntegerField()
    plan_type = serializers.ChoiceField(
        choices=PLAN_TYPE_CHOICES,
        help_text="Type of plan: 'text' or 'image'"
    )