# from apps.helpers.profile_info import ProfileInfoHelper
# from charset_normalizer.md import annotations
# from django.db import transaction
# from django.utils.timezone import now
# from rest_framework import status, permissions, generics
# from rest_framework.generics import get_object_or_404
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.views import APIView
# from urllib3 import request
#
# from apps.image_annotation.helpers.task_submission import AnnotationService
# from apps.image_annotation.helpers.task_assignment import TaskAssigner
# # from apps.image_annotation.models.plan_img_classification import ImageClassificationPlan
# from apps.image_annotation.models.task_img_classification import ImageClassificationTask, ImageClassificationAnnotation
# from apps.image_annotation.serializers.annotation_img_classification import ImageClassificationAnnotationTaskSerializer, \
#     ImageAnnotationSubmitSerializer
# from apps.image_annotation.serializers.task_img_classification import ImageClassificationTaskSerializer
# from apps.project_management.models import BatchMembers
#
# from rest_framework.response import Response
#
#
# def get_membership_or_404(profile_id, plan):
#     return get_object_or_404(BatchMembers, profile=profile_id, batch=plan.batch)
#
# #todo before fetching the first tasks should pass the qualification tasks
# class NextTaskView(APIView):
#     """
#     Returns current in-progress annotation or claims the next one for this annotator.
#     Only one in-progress at a time (others remain assigned/pending).
#     """
#     permission_classes = [IsAuthenticated]
#     #
#     # def get(self, request, plan_id):
#     #     # plan = get_object_or_404(ImageClassificationPlan, id=plan_id)
#     #     profile_id = ProfileInfoHelper.get_profile_id_from_request(request)
#     #
#     #     annotation_service=AnnotationService()
#     #
#     #     # This claim_next_task now triggers the Auto-Assigner if the user has no tasks
#     #     # annotation = annotation_service.claim_next_task(profile_id, plan)
#     #     print("Annotation claimed:", annotation)
#     #
#     #     if not annotation:
#     #         return Response({"detail": "No tasks available"}, status=status.HTTP_204_NO_CONTENT)
#     #
#     #     # respond with the underlying task
#     #     task_data = ImageClassificationTaskSerializer(annotation.task, context={'request': request}).data
#     #     print("Task data prepared:", task_data)
#     #
#     #     return Response({"annotation_id": annotation.id, "task": task_data}, status=status.HTTP_200_OK)
#
# class ActiveAssignedTasks(APIView):
#     """
#     Show tasks already assigned to this annotator but not yet in-progress.
#     (Locked view – annotator cannot work on them until claimed.)
#     """
#     permission_classes = [IsAuthenticated]
#     #
#     # def get(self, request, plan_id):
#     #     plan = get_object_or_404(ImageClassificationPlan, id=plan_id)
#     #     profile_id = ProfileInfoHelper.get_profile_id_from_request(request)
#     #     member = get_object_or_404(BatchMembers, profile=profile_id, batch=plan.batch)
#     #
#     #     assigned_annotations = (
#     #         ImageClassificationAnnotation.objects
#     #         .select_related("task")
#     #         .filter(annotator=member, task__plan=plan, status="assigned")
#     #     )
#     #
#     #     if not assigned_annotations.exists():
#     #         return Response({"detail": "No active assigned tasks."}, status=status.HTTP_204_NO_CONTENT)
#     #
#     #     tasks = [
#     #         {
#     #             "annotation_id": ann.id,
#     #             "status": ann.status,
#     #             "task": ImageClassificationTaskSerializer(ann.task, context={'request': request}).data,
#     #         }
#     #         for ann in assigned_annotations
#     #     ]
#     #
#     #     return Response(tasks, status=status.HTTP_200_OK)
#
#
# class SubmitAnnotationView(APIView):
#     permission_classes = [IsAuthenticated]
#
#     def post(self, request, annotation_id):
#         serializer = ImageAnnotationSubmitSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         annotation_service=AnnotationService()
#
#         profile_id = ProfileInfoHelper.get_profile_id_from_request(request)
#         annotation_service.submit_annotation(profile_id, annotation_id, serializer.validated_data)
#
#         return Response({"message": "Submitted"}, status=status.HTTP_200_OK)
#
# class AnnotatorProgressAPIView(APIView):
#     permission_classes = [IsAuthenticated]
#     #
#     # def get(self, request, plan_id):
#     #     # member = get_object_or_404(BatchMembers,request.user.id, plan_id)
#     #     profile_id = ProfileInfoHelper.get_profile_id_from_request(request)
#     #
#     #     plan = ImageClassificationPlan.objects.get(id=plan_id)
#     #     member = get_object_or_404(BatchMembers,profile=profile_id,batch=plan.batch)
#     #     progress = ImageClassificationAnnotation.objects.progress_for_annotator(member, plan_id)
#     #     return Response(progress)
#
# class SkipImageClassificationTaskAPIView(APIView):
#     """Mark a task as skipped."""
#     serializer_class = ImageAnnotationSubmitSerializer
#     permission_classes = [IsAuthenticated]
#
#     def get(self,request,annotation_id):
#         profile_id =ProfileInfoHelper.get_profile_id_from_request(request)
#         return ImageClassificationAnnotation.objects.filter(
#             annotator__profile=profile_id,
#             status="in_progress",
#             id=annotation_id
#         )
#
#     def perform_update(self, serializer):
#         serializer.save(status="skipped", updated_at=now())
#
# #todo by manager/team leader/admin role
# class FetchImageClassificationTaskAPIView(APIView):
#     """
#     Fetch single task details through assigned annotator, reviewer or manager role .
#     """
#     permission_classes = [IsAuthenticated]
#     #
#     # def get(self, request, plan_id, task_id):
#     #     plan = get_object_or_404(ImageClassificationPlan, id=plan_id)
#     #     profile_id = ProfileInfoHelper.get_profile_id_from_request(request)
#     #     membership = get_membership_or_404(profile_id, plan)
#     #     task = get_object_or_404(ImageClassificationTask, id=task_id, plan_id=plan_id)
#     #
#     #     serializer = ImageClassificationAnnotationTaskSerializer(
#     #         task,
#     #         context={"membership": membership, "include_progress": True}
#     #     )
#     #     return Response(serializer.data, status=status.HTTP_200_OK)


from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.helpers.profile_info import ProfileInfoHelper
from apps.image_annotation.models.task_annotation import ImageTaskAnnotation
from apps.image_annotation.serializers.annotation_submission import ImageAnnotationSubmissionSerializer
from apps.image_annotation.serializers.annotation_task import ImageAnnotationTaskSerializer
from apps.project_management.models.plan_members import PlanMember


# Helpers


# Services (Optional: logic moved inside views for clarity, can be extracted back to Service)
# from apps.image_annotation.services import AnnotationService


def get_worker_member(profile_id, batch_id):
    """Helper to get the BatchMember object for the annotator."""
    return get_object_or_404(
        PlanMember,
        profile=profile_id,
        batch_id=batch_id,
        role="ANNOTATOR"  # Adjust based on your Role choices
    )


class NextTaskView(APIView):
    """
    Returns the current IN_PROGRESS task or starts the next available ASSIGNED task.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, batch_id):
        profile_id = ProfileInfoHelper.get_profile_id_from_request(request)
        member = get_worker_member(profile_id, batch_id)

        # 1. Check if user already has a submission IN_PROGRESS
        # We look for an assignment where the *latest* submission is IN_PROGRESS
        current_assignment = ImageTaskAnnotation.objects.filter(
            annotator=member,
            submissions__status="IN_PROGRESS"
        ).order_by('-submissions__created_at').first()

        if current_assignment:
            # Return the existing work
            serializer = ImageAnnotationTaskSerializer(
                current_assignment,
                context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_200_OK)

        # 2. If no work in progress, find the next "Pending" assignment
        # (An assignment that has NO submissions yet)
        next_assignment = ImageTaskAnnotation.objects.filter(
            annotator=member,
            submissions__isnull=True
        ).first()

        if not next_assignment:
            # Optional: Trigger Auto-Assigner here if needed
            return Response({"detail": "No tasks currently assigned to you."}, status=status.HTTP_204_NO_CONTENT)

        # 3. "Start" the task by creating the initial Submission
        with transaction.atomic():
            ImageTaskAnnotation.objects.create(
                assigned_annotation=next_assignment,
                status="IN_PROGRESS",
                annotated_data={}  # Empty payload to start
            )

        serializer = ImageAnnotationTaskSerializer(
            next_assignment,
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


class ActiveAssignedTasks(APIView):
    """
    List tasks assigned to the user that they haven't started yet.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, batch_id):
        profile_id = ProfileInfoHelper.get_profile_id_from_request(request)
        member = get_worker_member(profile_id, batch_id)

        # Assignments with NO submissions are "Fresh/Pending"
        assigned_tasks = ImageTaskAnnotation.objects.filter(
            annotator=member,
            submissions__isnull=True
        )

        if not assigned_tasks.exists():
            return Response({"detail": "No active assigned tasks."}, status=status.HTTP_204_NO_CONTENT)

        serializer = ImageAnnotationTaskSerializer(
            assigned_tasks,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


class SubmitAnnotationView(APIView):
    """
    Saves the result and marks the task as SUBMITTED.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, task_id):
        # Note: task_id here refers to the Assignment ID (ImageAnnotationTask.id)
        profile_id = ProfileInfoHelper.get_profile_id_from_request(request)

        # Verify ownership
        assignment = get_object_or_404(
            ImageTaskAnnotation,
            id=task_id,
            annotator__profile=profile_id
        )

        # Get the IN_PROGRESS submission
        submission = assignment.submissions.filter(status="IN_PROGRESS").last()

        if not submission:
            return Response(
                {"detail": "No in-progress submission found for this task. Please start the task first."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update the submission using your Serializer logic (handling JSON packing)
        # We merge request data with status='SUBMITTED'
        data = request.data.copy()
        data['status'] = 'SUBMITTED'

        serializer = ImageAnnotationSubmissionSerializer(
            submission,
            data=data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({"message": "Annotation submitted successfully."}, status=status.HTTP_200_OK)


class AnnotatorProgressAPIView(APIView):
    """
    Calculates progress for the current batch.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, batch_id):
        profile_id = ProfileInfoHelper.get_profile_id_from_request(request)
        member = get_worker_member(profile_id, batch_id)

        # Base Query: All tasks assigned to this user in this batch
        # We filter assignments that link to tasks in this batch
        # (Assuming ImageAnnotationTask -> ImageBatchTask -> Batch)
        # Wait: ImageAnnotationTask links to ImageBatchTask. ImageBatchTask links to Batch.

        total_assigned = ImageTaskAnnotation.objects.filter(
            annotator=member,
            batch_item__batch_id=batch_id
        ).count()

        # Completed: Assignments where the LATEST submission is SUBMITTED or ACCEPTED
        # A simple approximation is checking if ANY submission is submitted/accepted
        # ideally we check the distinct count of assignments
        completed = ImageTaskAnnotation.objects.filter(
            annotator=member,
            batch_item__batch_id=batch_id,
            submissions__status__in=['SUBMITTED', 'ACCEPTED']
        ).distinct().count()

        remaining = total_assigned - completed

        return Response({
            "annotator_id": member.id,
            "total_assigned": total_assigned,
            "total_completed": completed,
            "remaining": remaining,
            "progress_percent": round((completed / total_assigned * 100), 2) if total_assigned else 0
        }, status=status.HTTP_200_OK)


class SkipImageClassificationTaskAPIView(APIView):
    """
    Mark the current task as SKIPPED (Custom Status) or REJECTED.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, task_id):
        profile_id = ProfileInfoHelper.get_profile_id_from_request(request)

        # Verify ownership
        assignment = get_object_or_404(
            ImageTaskAnnotation,
            id=task_id,
            annotator__profile=profile_id
        )

        submission = assignment.submissions.filter(status="IN_PROGRESS").last()
        if not submission:
            return Response({"detail": "Task is not in progress."}, status=400)

        # You might want to add "SKIPPED" to your STATUS_CHOICES in the model
        # For now, I will use a placeholder string or update via serializer
        submission.status = "SKIPPED"  # Ensure this is in your model choices!
        submission.annotated_data = {"skipped_reason": request.data.get("reason", "No reason provided")}
        submission.save()

        return Response({"message": "Task skipped."}, status=status.HTTP_200_OK)