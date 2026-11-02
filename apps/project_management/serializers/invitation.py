from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta
import secrets
from django.contrib.contenttypes.models import ContentType
from apps.profile.models.profile import Profile

from apps.project_management.models.invitation import PlanInvitation
from apps.project_management.utils.invitation import send_invitation_email


class PlanInvitationSerializer(serializers.ModelSerializer):
    """Single invitation serializer (backward compatibility)"""
    plan_type = serializers.CharField(write_only=True)
    plan_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = PlanInvitation
        fields = ['id', 'plan_type', 'plan_id', 'email', 'role', 'status', 'invited_by', 'expires_at','created_at','updated_at']
        read_only_fields = ['id', 'status', 'invited_by', 'created_at', 'expires_at', 'token','updated_at']
    
    def validate(self, attrs):
        # Get the content type from the plan_type
        try:
            content_type = ContentType.objects.get(model=attrs['plan_type'].lower())
        except ContentType.DoesNotExist:
            raise serializers.ValidationError(f"Invalid plan type: {attrs['plan_type']}")
            
        # Check if invitation already exists and is pending
        existing = PlanInvitation.objects.filter(
            content_type=content_type,
            object_id=attrs['plan_id'],
            email=attrs['email'],
            status='pending'
        ).exists()
        
        if existing:
            raise serializers.ValidationError("A pending invitation already exists for this email.")
            
        return attrs
    
    def create(self, validated_data):
        request = self.context.get('request')
        content_type = ContentType.objects.get(model=validated_data.pop('plan_type').lower())
        
        invitation = PlanInvitation(
            content_type=content_type,
            object_id=validated_data.pop('plan_id'),
            **validated_data,
            token=secrets.token_urlsafe(32),
            invited_by=request.user.id,
            expires_at=timezone.now() + timedelta(days=7)  # 7 days expiration
        )
        invitation.save()
        return invitation


class BulkPlanInvitationSerializer(serializers.Serializer):
    """Serializer for bulk invitations with multiple emails and profile selections"""
    plan_type = serializers.CharField()
    plan_id = serializers.IntegerField()
    emails = serializers.ListField(
        child=serializers.EmailField(),
        required=False,
        help_text="List of email addresses to invite"
    )
    profile_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="List of existing profile IDs to invite"
    )
    role = serializers.ChoiceField(
        choices=["Annotator", "Reviewer"],
        help_text="Role for all invitees"
    )
    
    def validate(self, attrs):
        emails = attrs.get('emails', [])
        profile_ids = attrs.get('profile_ids', [])
        
        if not emails and not profile_ids:
            raise serializers.ValidationError(
                "Please provide either 'emails' or 'profile_ids'."
            )
        
        if attrs['plan_type'].lower() == 'text':
            plan_model='textplan'
        elif attrs['plan_type'].lower() == 'image':
            plan_model='imageplan'
        elif attrs['plan_type'].lower() == 'audio':
            plan_model='audioplan'
        else:
            raise serializers.ValidationError(f"Invalid plan type: {attrs['plan_type']}")
        
        try:
            ContentType.objects.get(model=plan_model)
        except ContentType.DoesNotExist:
            raise serializers.ValidationError(f"Invalid plan type: {attrs['plan_type']}")
        
        # Validate profile_ids exist
        if profile_ids:
            existing_profiles = Profile.objects.filter(id__in=profile_ids).count()
            if existing_profiles != len(profile_ids):
                raise serializers.ValidationError(
                    f"Some profile IDs do not exist. Found {existing_profiles} out of {len(profile_ids)}."
                )
        
        return attrs
    
    def create(self, validated_data):
        """Create multiple invitations"""
        request = self.context.get('request')
        
        if validated_data['plan_type'].lower() == 'text':
            plan_model='textplan'
        elif validated_data['plan_type'].lower() == 'image':
            plan_model='imageplan'
        elif validated_data['plan_type'].lower() == 'audio':
            plan_model='audioplan'
        else:
            raise serializers.ValidationError(f"Invalid plan type: {validated_data['plan_type']}")

        content_type = ContentType.objects.get(model=plan_model)
        
        emails = validated_data.get('emails', [])
        profile_ids = validated_data.get('profile_ids', [])
        role = validated_data['role']
        plan_id = validated_data['plan_id']
        
        invitations = []
        invited_emails = set()
        
        # Get emails from profile_ids
        if profile_ids:
            profiles = Profile.objects.filter(id__in=profile_ids)
            for profile in profiles:
                if profile.email:
                    invited_emails.add(profile.email)
        
        # Add manually provided emails
        for email in emails:
            invited_emails.add(email)
        
        # Create invitations for all unique emails
        for email in invited_emails:
            # Check if invitation already exists and is pending
            existing = PlanInvitation.objects.filter(
                content_type=content_type,
                object_id=plan_id,
                email=email,
                status='pending'
            ).exists()
                            
            if not existing:
                invitation = PlanInvitation(
                    content_type=content_type,
                    object_id=plan_id,
                    email=email,
                    role=role,
                    token=secrets.token_urlsafe(32),
                    invited_by=request.user.id,
                    expires_at=timezone.now() + timedelta(days=7)
                )
                invitation.save()
                send_invitation_email(invitation)
                invitations.append(invitation)
        
        return {
            'count': len(invitations),
            'invitations': invitations,
            'skipped': len(invited_emails) - len(invitations)
        }

class PlanInvitationResponseSerializer(serializers.Serializer):
    """
    Serializer for handling invitation responses (accept/decline)
    """
    token = serializers.CharField()
    action = serializers.ChoiceField(choices=['accept', 'decline'])
    
    def validate_token(self, value):
        try:
            return PlanInvitation.objects.get(token=value, status='pending')
        except PlanInvitation.DoesNotExist:
            raise serializers.ValidationError("Invalid or expired invitation token.")
        except PlanInvitation.MultipleObjectsReturned:
            # This should never happen due to unique constraint
            raise serializers.ValidationError("Invalid invitation.")