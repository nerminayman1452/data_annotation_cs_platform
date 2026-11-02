from rest_framework import serializers

from apps.image_annotation.models.task_annotation import ImageTaskAnnotation
from apps.project_management.models.image_plan import ImageLabelType


class ImageAnnotationSubmissionSerializer(serializers.ModelSerializer):
    # 1. Virtual Fields (Input from Frontend)
    # These do not exist on the model anymore, but we accept them here
    label_type_result = serializers.PrimaryKeyRelatedField(
        queryset=ImageLabelType.objects.all(),
        required=False,
        allow_null=True,
        write_only=True
    )
    custom_label = serializers.CharField(
        required=False,
        allow_blank=True,
        write_only=True
    )

    # 2. Virtual Fields (Output to Frontend)
    # We unpack the JSON back into these fields for reading
    result_display = serializers.SerializerMethodField()

    class Meta:
        model = ImageTaskAnnotation
        fields = [
            "id",
            "status",
            "spent_time",
            # Inputs
            "label_type_result",
            "custom_label",
            # Outputs
            "result_display",
            "annotated_data",  # Optional: keep if you want to see the raw JSON
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["status", "created_at", "updated_at", "annotated_data"]

    def validate(self, attrs):
        """
        Preserve your exact old validation logic.
        """
        label_type = attrs.get('label_type_result')
        custom_label = attrs.get('custom_label')

        # Check if we are creating/updating payload
        # (Skip check if we are just updating status)
        if 'label_type_result' in attrs or 'custom_label' in attrs:
            if not label_type and not custom_label:
                raise serializers.ValidationError(
                    "You must provide either a predefined label or a custom label."
                )
            if label_type and custom_label:
                raise serializers.ValidationError(
                    "Provide either a predefined label or custom label, not both."
                )

        return attrs

    def create(self, validated_data):
        """
        Pack the specific fields into the generic JSON field.
        """
        label_type = validated_data.pop('label_type_result', None)
        custom_label = validated_data.pop('custom_label', None)

        # Construct the JSON payload
        payload = {}
        if label_type:
            payload['label_id'] = label_type.id
            payload['label_text'] = label_type.label_type  # Store text too for easier reading
            payload['type'] = 'predefined'
        elif custom_label:
            payload['custom_text'] = custom_label
            payload['type'] = 'custom'

        validated_data['annotated_data'] = payload
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """
        Handle updates to the JSON payload.
        """
        label_type = validated_data.pop('label_type_result', None)
        custom_label = validated_data.pop('custom_label', None)

        if label_type or custom_label:
            payload = {}
            if label_type:
                payload['label_id'] = label_type.id
                payload['label_text'] = label_type.label_type
                payload['type'] = 'predefined'
            elif custom_label:
                payload['custom_text'] = custom_label
                payload['type'] = 'custom'

            validated_data['annotated_data'] = payload

        return super().update(instance, validated_data)

    def get_result_display(self, obj):
        """
        Unpack the JSON for the frontend to display nicely.
        """
        data = obj.annotated_data or {}
        if data.get('type') == 'predefined':
            return {
                "label_id": data.get('label_id'),
                "label_text": data.get('label_text'),
                "is_custom": False
            }
        elif data.get('type') == 'custom':
            return {
                "label_text": data.get('custom_text'),
                "is_custom": True
            }
        return None