from rest_framework import serializers

class BaseTaskAnnotationSerializer(serializers.ModelSerializer):
    member = serializers.StringRelatedField()

    class Meta:
        fields = [
            "id",
            "member",
            "status",
            "spent_time",
            "annotated_data",
            "created_at",
            "updated_at",
        ]
