from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from apps.project_management.models.plan_members import PlanMember
from apps.profile.models.profile import Role
from services.auth_service.client import get_user_info


class PlanMembersSerializer(serializers.ModelSerializer):
    profile = serializers.IntegerField(required=True, help_text="User Profile ID")
    role = serializers.ChoiceField(choices=Role.choices, default=Role.ANNOTATOR)

    # Read-only fields for display
    user_info = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = PlanMember
        fields = ['id', 'profile', 'role', 'user_info']
        read_only_fields = ['id', 'user_info']

    def get_user_info(self, obj):
        """
        Fetch user details from the Auth Service.
        Note: For listing many members, this can be slow. 
         Ideally, fetch in bulk in the View.
        """
        # If the view already injected user_data (bulk fetch), use it
        if hasattr(obj, 'cached_user_info'):
            return obj.cached_user_info

        # Fallback to individual fetch
        request = self.context.get('request')
        token = request.headers.get("Authorization", "").split(" ")[-1] if request else ""
        try:
            return get_user_info(obj, token)
        except Exception:
            return None

    def validate(self, attrs):
        request = self.context.get('request')
        plan = self.context.get('plan')  # This is the specific TextPlan or ImagePlan object
        profile_id = attrs.get('profile')

        # 1. Validation: Plan must exist (handled by View context)
        if not plan:
            raise serializers.ValidationError("Plan context is missing.")

        # 2. Validation: Only the Creator can add members
        # Note: Ensure your Plan models have 'created_by'
        if hasattr(plan, 'created_by') and plan.created_by != int(request.user.id):
            raise serializers.ValidationError("You are not authorized to assign members to this plan.")

        # 3. Validation: Check if User exists in Auth Service
        token = request.headers.get("Authorization", "").split(" ")[-1]
        user_info = get_user_info(profile_id, token)
        if user_info is None:
            raise serializers.ValidationError(f"User profile {profile_id} does not exist.")

        # 4. Validation: Unique Constraint (Profile + Plan)
        # We must check content_type + object_id manually
        ct = ContentType.objects.get_for_model(plan)
        if PlanMember.objects.filter(
                content_type=ct,
                object_id=plan.id,
                profile=profile_id
        ).exists():
            raise serializers.ValidationError(f"User {profile_id} is already a member of this plan.")

        return attrs

    def create(self, validated_data):
        """
        Create the Generic Link.
        """
        plan = self.context.get('plan')
        validated_data['plan'] = plan  # GenericForeignKey assignment magic
        return super().create(validated_data)


class PlanMembersBulkSerializer(serializers.Serializer):
    """
    Helper serializer specifically for the POST request (adding multiple users).
    """
    profiles = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="List of User Profile IDs to add"
    )
    role = serializers.ChoiceField(choices=Role.choices, default=Role.ANNOTATOR)
