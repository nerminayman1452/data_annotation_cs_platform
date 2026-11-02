from rest_framework import serializers

from apps.project_management.models.organization import Organization


class OrganizationSerializer(serializers.ModelSerializer):
    # created_by = serializers.PrimaryKeyRelatedField(read_only=True)
    created_by = serializers.IntegerField(read_only=True)

    class Meta:
        model = Organization
        fields = ['id', 'name', 'contact_email', 'is_active', 'created_by', ]

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Organization name cannot be empty.")
        return value

    def validate_contact_email(self, value):
        value = value.strip().lower()
        if Organization.objects.filter(contact_email__iexact=value).exists():
            raise serializers.ValidationError("This contact email is already in use.")
        return value

    def create(self, validated_data):
        user = self.context['request'].user
        return Organization.objects.create(
            created_by=user.id,
            **validated_data
        )
