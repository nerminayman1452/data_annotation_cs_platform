import logging
from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from drf_spectacular.utils import extend_schema, OpenApiResponse
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q

from apps.project_management.models.invitation import PlanInvitation
from apps.project_management.models.plan_members import PlanMember
from apps.project_management.serializers.invitation import (
    PlanInvitationSerializer,
    BulkPlanInvitationSerializer,
    PlanInvitationResponseSerializer
)
from apps.project_management.utils.invitation import send_invitation_email

logger = logging.getLogger(__name__)

@extend_schema(
    tags=['Plan Invitations'],
    description='Create a new plan invitation',
    responses={
        201: PlanInvitationSerializer()
    }
)
class PlanInvitationCreateView(generics.CreateAPIView):
    """
    Create a new plan invitation.
    Only plan owners/reviewers can invite users.
    """
    serializer_class = PlanInvitationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return PlanInvitation.objects.all()

    def perform_create(self, serializer):
        # The create method in the serializer will handle the rest
        invitation = serializer.save()
        send_invitation_email(invitation)
    

@extend_schema(
    tags=['Plan Invitations'],
    description='Create bulk invitations - invite multiple members at once',
    request=BulkPlanInvitationSerializer,
    responses={
        201: OpenApiResponse(
            description="Bulk invitations created successfully",
            examples={
                "application/json": {
                    "count": 3,
                    "skipped": 1,
                    "detail": "Successfully created 3 invitations. 1 invitation(s) skipped (already pending)."
                }
            }
        ),
        400: OpenApiResponse(
            description="Invalid request",
            examples={
                "application/json": {
                    "detail": "Please provide either 'emails' or 'profile_ids'."
                }
            }
        )
    }
)
class BulkPlanInvitationCreateView(APIView):
    """
    Create bulk invitations for a plan.
    Allows inviting multiple members using emails and/or existing profile IDs.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        serializer = BulkPlanInvitationSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        result = serializer.save()
        # invitations = result['invitations']
        
        # # Send invitation emails
        # for invitation in invitations:
        #     send_invitation_email(invitation)
        
        return Response({
            'count': result['count'],
            'skipped': result['skipped'],
            'detail': f"Successfully created {result['count']} invitations. {result['skipped']} invitation(s) skipped (already pending)."
        }, status=status.HTTP_201_CREATED)
    
@extend_schema(
    tags=['Plan Invitations'],
    description='List all invitations for a plan',
    responses={
        200: PlanInvitationSerializer(many=True)
    }
)
class PlanInvitationListView(generics.ListAPIView):
    """
    List all invitations for a plan
    """
    serializer_class = PlanInvitationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.kwargs['plan_type'] == 'text':
            content_type = ContentType.objects.get(model='textplan')   
        elif self.kwargs['plan_type'] == 'image':
            content_type = ContentType.objects.get(model='imageplan') 
        else:
            return PlanInvitation.objects.none()  # Return empty queryset for invalid plan types

        return PlanInvitation.objects.filter(
            content_type=content_type,
            object_id=self.kwargs['plan_id']
        )


@extend_schema(
    tags=['Plan Invitations'],
    description='Handle invitation acceptance/decline',
    request=PlanInvitationResponseSerializer,
    responses={
        200: OpenApiResponse(
            description="Invitation processed successfully",
            examples={
                "application/json": {
                    "detail": "Invitation accepted successfully."
                }
            }
        ),
        400: OpenApiResponse(
            description="Invalid request or invitation",
            examples={
                "application/json": {
                    "detail": "This invitation has expired."
                }
            }
        )
    }
)
class PlanInvitationResponseView(APIView):
    """
    Handle invitation acceptance/decline.
    Accepts a token and action (accept/decline) to process the invitation.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        request=PlanInvitationResponseSerializer,
        responses={
            200: OpenApiResponse(
                description="Success response",
                examples={
                    "application/json": {
                        "detail": "Invitation accepted successfully."
                    }
                }
            ),
            400: OpenApiResponse(
                description="Error response",
                examples={
                    "application/json": {
                        "detail": "This invitation has expired."
                    }
                }
            )
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = PlanInvitationResponseSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        invitation = serializer.validated_data['token']
        action = serializer.validated_data['action']
        
        if invitation.is_expired():
            invitation.status = 'expired'
            invitation.save()
            return Response(
                {"detail": "This invitation has expired."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if action == 'accept':
            return self._handle_accept(invitation, request.user.id)
        else:
            return self._handle_decline(invitation)
    
    def _handle_accept(self, invitation, user_id):
        # Check if user is already a member
        if PlanMember.objects.filter(
            profile=user_id, 
            content_type=invitation.content_type,
            object_id=invitation.object_id
        ).exists():
            return Response(
                {"detail": "You are already a member of this plan."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Add user to plan members
        # Add user to plan members
        PlanMember.objects.create(
            profile=user_id,
            content_type=invitation.content_type,
            object_id=invitation.object_id,
            role=invitation.role
        )
        
        # Update invitation status
        invitation.status = 'accepted'
        invitation.save()
        
        return Response({"detail": "Invitation accepted successfully."})
    
    def _handle_decline(self, invitation):
        invitation.status = 'declined'
        invitation.save()
        return Response({"detail": "Invitation declined."})