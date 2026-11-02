from rest_framework.views import APIView
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count, Q

from apps.helpers.profile_info import ProfileInfoHelper
from apps.project_management.models import Batch, PlanMember
from apps.dashboard.serializers.dashboard import BatchCardSerializer
from apps.dashboard.helpers.stats import UserStatsCalculator
# from apps.image_annotation.models.plan_img_object_detection import ObjectDetectionPlan
# from apps.image_annotation.models.plan_img_polygons import PolygonPlan
# from apps.text_annotation.models.plan_text_labelling import TextLabellingPlan
# from apps.text_annotation.models.plan_text_summarization import TextSummarizationPlan
# from apps.text_annotation.models.plan_text_validation import TextValidationPlan
# from apps.text_annotation.models.plan_text_segmentation import TextSegmentationPlan
from apps.audio_annotation.models.plan_audio_labelling import AudioLabellingPlan
from apps.audio_annotation.models.plan_audio_segmentation import AudioSegmentationPlan
from apps.audio_annotation.models.plan_audio_transcription import AudioTranscriptionPlan
from apps.audio_annotation.models.plan_audio_speaker_diarization import AudioSpeakerDiarizationPlan
from apps.dashboard.helpers.plan_utils import PlanInspector
from apps.dashboard.services.dashboard_service import DashboardService


class AnnotatorDashboardAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_id = getattr(request.user, "id", None)
        profile_id = ProfileInfoHelper.get_profile_id_from_request(request)

        member_id = DashboardService.get_member_id(profile_id)

        # Calculate user stats using all annotation models from PlanInspector
        user_stats = DashboardService.get_user_stats(member_id)

        active_batches = DashboardService.get_active_batches(request, member_id)

        # Collect recent plans across all plan models
        recent_plans = DashboardService.get_recent_plans(member_id, limit_per_model=10, top_n=10)

        payload = {
            "xp_points": user_stats.xp_points,
            "datcoins": user_stats.datcoins,
            "level": user_stats.level,
            "accuracy": user_stats.accuracy,
            "level_progress": user_stats.level_progress,  # Add progress towards next level
            "active_batches": active_batches,
            "recent_plans": list(recent_plans),
        }
        return Response(payload)

class UserStatsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_id = getattr(request.user, "id", None)
        profile_id = ProfileInfoHelper.get_profile_id_from_request(request)

        member_id = DashboardService.get_member_id(profile_id)

        # Calculate user stats using all annotation models from PlanInspector
        user_stats = DashboardService.get_user_stats(member_id)

        payload = {
            "xp_points": user_stats.xp_points,
            "datcoins": user_stats.datcoins,
            "level": user_stats.level,
            "accuracy": user_stats.accuracy,
            "level_progress": user_stats.level_progress,  # Add progress towards next level
            "all_tasks": user_stats.all_tasks,
            "all_submitted": user_stats.all_submitted,
            "all_approved": user_stats.all_approved,
            "all_rejected": user_stats.all_rejected,
        }
        return Response(payload)

class MyActiveProgressAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        member_id = DashboardService.get_member_id(user.id)
        if not member_id:
            return Response({"detail": "User is not a member of any batch."}, status=404)

        batches = DashboardService.get_my_active_batches(request, member_id)
        recent_plans = DashboardService.get_my_recent_plans(member_id)

        return Response({
            "batches": batches,
            "recent_plans": recent_plans,
        })

class BatchDetailsAPIView(RetrieveAPIView):
    """
    Return detailed info about a single batch, including its plans and members.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = BatchCardSerializer
    queryset = Batch.objects.all()

    def get(self, request, batch_id, *args, **kwargs):
        try:
            batch = self.get_queryset().get(pk=batch_id)
        except Batch.DoesNotExist:
            return Response({"error": "Batch not found"}, status=404)

        membership = (
            PlanMember.objects
            .filter(profile=request.user.id, batch=batch)
            .values_list("id", flat=True)
            .first()
        )

        serializer = self.serializer_class(
            batch,
            context={"request": request, "membership": membership}
        )
        return Response(serializer.data)