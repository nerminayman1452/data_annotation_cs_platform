from django.core.mail import send_mail
from django.conf import settings
import logging
logger = logging.getLogger(__name__)


# def send_invitation_email(invitation):
#     try:
#         # 1. Get the actual plan object via GenericForeignKey
#         plan_obj = invitation.plan
        
#         # 2. Extract name: Check for 'name' attribute, fallback to __str__, then fallback to ID
#         if plan_obj:
#             plan_name = getattr(plan_obj, 'name', str(plan_obj))
#         else:
#             plan_name = f"Plan #{invitation.object_id}"

#         subject = f"Invitation to join plan: {plan_name}"
#         message = f"""
#         You have been invited to join the plan "{plan_name}" as a {invitation.role}.
#         To accept this invitation, click the following link:
#         {settings.FRONTEND_BASE_URL}/invitations/accept/{invitation.token}/
#         This invitation will expire on {invitation.expires_at.strftime('%Y-%m-%d %H:%M')}.
#         """
#         send_mail(
#             subject,
#             message.strip(),
#             settings.DEFAULT_FROM_EMAIL,
#             [invitation.email],
#             fail_silently=False,
#         )
#         logger.info(f"Invitation email sent to {invitation.email} for plan {plan_name}")
            
#     except Exception as e:
#         logger.error(f"Failed to send email to {invitation.email}: {str(e)}")


def send_invitation_email(invitation):
    try:
        # Access the plan directly via GenericForeignKey
        plan = invitation.plan
        
        # Determine the best name to display
        # 1. Try plan.name (since it exists in BasePlan)
        # 2. Try str(plan) 
        # 3. Fallback to model type and ID
        if plan and hasattr(plan, 'name') and plan.name:
            plan_name = plan.name
        elif plan:
            plan_name = str(plan)
        else:
            plan_name = f"{invitation.content_type.model.title()} #{invitation.object_id}"

        subject = f"Invitation to join: {plan_name}"
        
        # Clean up the message (using .strip() and textwrap.dedent logic for better formatting)
        message = (
            f"You have been invited to join the plan \"{plan_name}\" as a {invitation.role}.\n\n"
            f"To accept this invitation, click the following link:\n"
            f"{settings.FRONTEND_BASE_URL}/invitations/accept/{invitation.token}/\n\n"
            f"This invitation will expire on {invitation.expires_at.strftime('%Y-%m-%d %H:%M')}."
        )
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [invitation.email],
            fail_silently=False,
        )
        logger.info(f"Email sent successfully to {invitation.email} for plan: {plan_name}")
            
    except Exception as e:
        logger.error(f"Failed to send email to {invitation.email}: {str(e)}", exc_info=True)

