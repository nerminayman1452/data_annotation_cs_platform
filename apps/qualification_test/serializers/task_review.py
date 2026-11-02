from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404

from apps.project_management.models.plan_members import PlanMember
from apps.project_management.models.batch import Batch
from apps.profile.models.profile import Profile
from apps.qualification_test.models.exam import ExamBatchMembers, ExamTaskReview
from apps.qualification_test.serializers.task import ExamTaskSerializer


class AssignExamReviewerSerializer(serializers.Serializer):
    annotator_exam_member_id = serializers.IntegerField(help_text="ID of the annotator (ExamReviewBatchMember)")
    reviewer_id = serializers.IntegerField(help_text="ID of the reviewer (Profile or batch owner)")
    batch_id = serializers.IntegerField(help_text="ID of the batch where exam belongs")

    def validate(self, attrs):
        annotator_exam_member_id = attrs.get("annotator_exam_member_id")
        reviewer_id = attrs.get("reviewer_id")
        batch_id = attrs.get("batch_id")

        exam_member = ExamBatchMembers.objects.filter(id=annotator_exam_member_id).select_related("exam").first()
        #todo profile
        reviewer = Profile.objects.filter(id=reviewer_id).first()
        batch = Batch.objects.filter(id=batch_id).select_related("owner", "exam").first()

        if not exam_member:
            raise ValidationError("Annotator exam member not found.")
        if not reviewer:
            raise ValidationError("Reviewer not found.")
        if not batch:
            raise ValidationError("Batch not found.")

        if batch.exam != exam_member.exam:
            raise ValidationError("The annotator exam member does not belong to this batch's exam.")

        if reviewer != batch.owner:
            member = PlanMember.objects.filter(
                batch=batch, profile=reviewer, role__in=["REVIEWER", "SUPER_REVIEWER"]
            ).first()
            if not member:
                raise ValidationError("Reviewer must be the batch owner or a member with role reviewer/super-reviewer.")

        attrs["exam_member"] = exam_member
        attrs["reviewer"] = reviewer
        attrs["batch"] = batch
        return attrs


class ExamTaskReviewDecisionSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(
        choices=[("ACCEPTED", "Accepted"), ("REJECTED", "Rejected")]
    )
    feedback = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        review_id = self.context.get("review_id")
        review = get_object_or_404(ExamTaskReview, id=review_id)

        if review.decision != "PENDING":
            raise serializers.ValidationError("This review was already submitted.")

        reviewer_user = self.context["request"].user
        if review.reviewer.user_id != int(reviewer_user.id):
            raise serializers.ValidationError("You are not assigned to this review.")

        data["review"] = review
        return data

    def save(self):
        review = self.validated_data["review"]

        review.decision = self.validated_data["decision"]
        review.feedback = self.validated_data.get("feedback", "")
        review.save(update_fields=["decision", "feedback", "updated_at"])

        task = review.plan
        if review.decision == "ACCEPTED":
            task.status = "CORRECT_EXAM_ANSWER"
        else:
            task.status = "WRONG_EXAM_ANSWER"

        task.save(update_fields=["status", "updated_at"])

        return review

    def to_representation(self, review):
        task = review.plan
        return {
            "review_id": review.id,
            "task_id": task.id,
            "reviewer": review.reviewer.id,
            "decision": review.decision,
            "feedback": review.feedback,
            "question": task.question.id,
            "annotator_answer": task.answer,
            "task_status": task.status,
            "updated_at": review.updated_at,
        }


class ExamTaskReviewSerializer(serializers.ModelSerializer):
    #todo profile
    # reviewer = serializers.PrimaryKeyRelatedField(
    #     queryset=Profile.objects.all()
    # )
    task = ExamTaskSerializer(read_only=True)


    class Meta:
        model = ExamTaskReview
        fields = [
            "id",
            "reviewer",
            "decision",
            "feedback",
            "created_at",
            "task",
        ]
