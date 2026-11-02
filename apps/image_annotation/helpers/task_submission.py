from django.db import transaction
from rest_framework.exceptions import PermissionDenied, NotFound

# from apps.image_annotation.models.task_img_classification import ImageClassificationAnnotation
from unused_scripts.image_task_assignment import TaskAssigner
from apps.project_management.models.plan_members import PlanMember


#1) Validator: Permissions & Ownership
class AnnotationValidator:
    @staticmethod
    def validate_ownership(annotation, profile_id):
        """Makes sure that the current user is the annotator who owns this annotation."""
        if not annotation.annotator or str(annotation.annotator.profile) != str(profile_id):
            raise PermissionDenied("Not permitted.")

    @staticmethod
    def validate_batch_membership(profile_id, plan):
        """
        Ensures the annotator belongs to the batch. 
        If not a member and batch is NOT locked, auto-join them.
        """
        member = PlanMember.objects.select_related("batch").filter(
            profile=profile_id, batch=plan.plan
        ).first()

        # If member does not exist...
        if not member:
            # Check if we can auto-join (Batch is NOT locked)
            # if not plan.batch.is_locked:
                # Create the new membership
                member = PlanMember.objects.create(
                    profile=profile_id,
                    batch=plan.plan,
                    # is_active=True,  # Ensure they are active immediately
                    user_role='Annotator' # Set default role if your model requires it
                )
            # else:
            #     # Batch is locked, so no new members allowed
            #     raise PermissionDenied("Not a batch member and batch is locked.")
                
        return member


#2) Repository: DB CRUD for Annotations
class AnnotationRepository:
    @staticmethod
    def get_annotation(annotation_id):
        """Fetches annotation, prefetching task + annotator for efficiency."""
        try:
            return ImageClassificationAnnotation.objects.select_related(
                "task", "annotator"
            ).get(id=annotation_id)
        except ImageClassificationAnnotation.DoesNotExist:
            raise NotFound("Annotation not found.")

    @staticmethod
    def get_in_progress(member, plan):
        """Checks if the annotator already has an in_progress task."""
        return (ImageClassificationAnnotation.objects
        #locks the row until transaction ends, prevents race conditions (two tasks being marked in progress at the same time)
                .select_for_update()
                .select_related("task")
                .filter(annotator=member, task__plan=plan, status="in_progress")
                .first())

    @staticmethod
    def get_assigned(member, plan):
        """
        Finds the next assigned task that still needs more annotations for this plan.
        Each annotator gets their own annotation row.
        """

        return (ImageClassificationAnnotation.objects
                # Uses skip_locked, skips rows already locked by another transaction (helps when multiple annotators are pulling tasks at once).
                .select_for_update()
                .select_related("task")
                # .order_by("created_at")  # or random
                .filter(annotator=member, task__plan=plan, status="assigned")
                .first())

    @staticmethod
    def save_annotation(annotation, validated_data):
        annotation.label_type_result = validated_data.get("label_type_result")
        annotation.custom_label = validated_data.get("custom_label")
        annotation.update_status("submitted")
        annotation.save()
        return annotation


# 3) Progress Tracker
class TaskProgressTracker:
    """Handles checking progress and triggering auto-assign."""

    def __init__(self, plan, annotation_type="classification"):
        self.plan = plan
        self.assigner = TaskAssigner(plan, annotation_type)

    def trigger_auto_assignment(self, annotator):
        """
        After an annotator submits, check if they finished their available tasks.
        If auto-mode is enabled, assign next batch.
        """
        self.assigner.auto_assign_next_tasks(annotator)
        return None


#4) Service: Orchestration
class AnnotationService:
    def __init__(self):
        self.validator = AnnotationValidator()
        self.repo = AnnotationRepository()

    def submit_annotation(self, profile_id, annotation_id, validated_data):
        """Submit result and move status -> submitted."""
        annotation = self.repo.get_annotation(annotation_id)
        self.validator.validate_ownership(annotation, profile_id)

        with transaction.atomic():
            saved = self.repo.save_annotation(annotation, validated_data)

            #handle auto-assign via TaskProgressTracker if submitted all his available tasks
            tracker = TaskProgressTracker(saved.plan.plan, "classification")
            tracker.trigger_auto_assignment(saved.annotator)

        return saved

    def claim_next_task(self, profile_id, plan):
        """Return current in-progress task or assign new one."""
        member = self.validator.validate_batch_membership(profile_id, plan)
        print("Member validated:", member)

        with transaction.atomic():
            # 1) Existing in_progress
            in_progress = self.repo.get_in_progress(member, plan)
            if in_progress:
                return in_progress

            # 2) Promote an 'assigned'
            assigned = self.repo.get_assigned(member, plan)
            if assigned:
                assigned.update_status("in_progress")
                return assigned
            else:
            # 4. NEW LOGIC: Just-In-Time Assignment
            # If we are here, the user has NO tasks. We must trigger the assigner.
                assigner = TaskAssigner(plan, "classification") # Or pass type dynamically if needed
                
                # This calls the method we fixed in Step 1
                new_tasks = assigner.assign_initial_tasks()
                print("New tasks assigned:", new_tasks)

                if new_tasks:
                    a = new_tasks[0]
                    a.update_status("in_progress")
                    return a


        return None
