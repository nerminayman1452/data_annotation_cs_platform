from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from apps.project_management.models.plan_members import PlanMember


class BaseImageAnnotationTaskSerializer(serializers.ModelSerializer):
    annotations = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()

    # MUST be overridden
    annotation_model = None

    class Meta:
        abstract = True

    # ---------- Shared logic ---------- #

    def _get_membership(self):
        membership = self.context.get("membership")
        if not membership:
            raise PermissionDenied("You are not part of this batch.")
        return membership

    def get_annotations(self, obj):
        membership = self._get_membership()

        role = (membership.user_role or "").lower()
        if role not in ["annotator", "reviewer"]:
            raise PermissionDenied("You don't have permission to view this task.")

        annots = obj.annotations.filter(annotator=membership)

        return [self.serialize_annotation(a) for a in annots]

    def get_progress(self, obj):
        membership = self._get_membership()

        if not self.context.get("include_progress"):
            return None

        if (membership.user_role or "").lower() != "annotator":
            raise PermissionDenied("You don't have permission to view the task progress.")

        return self.annotation_model.objects.progress_for_annotator(
            membership, obj.plan_id
        )

    # ---------- Overridden by subclasses ---------- #

    def serialize_annotation(self, annotation):
        raise NotImplementedError("serialize_annotation must be implemented")
