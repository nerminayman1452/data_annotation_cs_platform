
from apps.helpers.profile_info import ProfileInfoHelper
from apps.project_management.models import  PlanMember
from apps.dashboard.models.batch_join import BatchJoinRequest
from apps.project_management.models.batch import Batch


class BatchAccessManager:
    """Encapsulates all access control logic for batches."""

    def __init__(self,request):
        self.request = request
        
    @staticmethod
    def can_access_batch(batch: Batch, annotator_id: int) -> bool:
        """Check if the annotator can enter this batch directly."""
        if not batch.is_locked:
            return True
        if PlanMember.objects.filter(batch=batch, profile=annotator_id).exists():
            return True
        return False

    @staticmethod
    def get_access_status(batch: Batch, annotator_id: int) -> str:
        """Return access state string for dashboard display."""
        if BatchAccessManager.can_access_batch(batch, annotator_id):
            return "accessible"

        join_req = BatchJoinRequest.objects.filter(batch=batch, annotator=annotator_id).first()
        if join_req:
            return join_req.status  # 'pending', 'approved', 'rejected'
        return "locked"
    
    @staticmethod
    def has_pending_request(batch: Batch, annotator_id: int) -> bool:
        """Check if there is a pending join request for this annotator and batch."""
        return BatchJoinRequest.objects.filter(batch=batch, annotator=annotator_id, status="pending").exists()
    
    @staticmethod
    def has_approved_request(batch: Batch, annotator_id: int) -> bool:
        """Check if there is an approved join request for this annotator and batch."""
        return BatchJoinRequest.objects.filter(batch=batch, annotator=annotator_id, status="approved").exists()
    
    @staticmethod
    def has_rejected_request(batch: Batch, annotator_id: int) -> bool:
        """Check if there is a rejected join request for this annotator and batch."""
        return BatchJoinRequest.objects.filter(batch=batch, annotator=annotator_id, status="rejected").exists()
    
    @staticmethod
    def get_profile_info(request,annotator_id: int):
        print("Profile ID in BatchAccessManager:",annotator_id)
        return ProfileInfoHelper.get_profile_data_from_request(request,annotator_id).get("first_name"), ProfileInfoHelper.get_profile_data_from_request(request,annotator_id).get("last_name"), ProfileInfoHelper.get_profile_data_from_request(request,annotator_id).get("user").get("email")

    @staticmethod
    def check_existing_request(batch: Batch, annotator_id: int) -> BatchJoinRequest:
        """Return existing join request if any."""
        return BatchJoinRequest.objects.filter(batch=batch, annotator=annotator_id).first()

    @staticmethod
    def request_access(request, batch: Batch, annotator_id: int) -> BatchJoinRequest:
        """Create or reuse a pending join request."""

        if not BatchAccessManager.check_existing_request(batch, annotator_id):

            first_name, last_name, email = BatchAccessManager.get_profile_info(request,annotator_id)
            join_request, _ = BatchJoinRequest.objects.get_or_create(
                batch=batch,
                annotator=annotator_id,
                first_name= first_name,
                last_name= last_name,
                email= email,
                defaults={"status": "pending"}
            )
            return join_request
