from rest_framework import serializers
from ..models.profile import Profile, Role

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = '__all__'
        read_only_fields = ('created_at', 'modified_at')

    def validate_role(self, value):
        if value not in [role[0] for role in Role.choices]:
            raise serializers.ValidationError("Invalid role")
        return value
