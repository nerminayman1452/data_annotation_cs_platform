from rest_framework.generics import ListCreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from apps.text_annotation.services.review_text_validation import ReviewTextValidationGenerator
from apps.text_annotation.models.review_text_validation import ReviewTextValidationResult
# from apps.text_annotation.models.plan_text_validation import TextValidationPlan
from apps.text_annotation.models.task_text_validation import TextValidationTaskResult
from apps.text_annotation.serializers.review_text_validation import ReviewTextValidationResultSerializer


class ReviewTextValidationResultListCreateAPIView(ListCreateAPIView):
    serializer_class = ReviewTextValidationResultSerializer
    permission_classes = [IsAuthenticated]
    queryset = ReviewTextValidationResult.objects.all()

    def post(self, request, *args, **kwargs):
        plan_id = kwargs.get("plan_id")

        if not plan_id:
            return Response({"detail": "plan_id is required in the URL."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            plan = TextValidationPlan.objects.get(id=plan_id)
        except TextValidationPlan.DoesNotExist:
            return Response({"detail": "Plan not found."}, status=status.HTTP_404_NOT_FOUND)

        submitted_tasks = TextValidationTaskResult.objects.filter(plan_validation=plan, status='submitted')

        if not submitted_tasks.exists():
            return Response({"message": "No submitted tasks found for this plan."}, status=status.HTTP_404_NOT_FOUND)

        task_reviews = ReviewTextValidationGenerator()
        created_reviews = []

        for task in submitted_tasks:
            try:
                created_reviews.extend(task_reviews.create_reviews_to_task(task))
            except ValueError:
                continue

        serializer = self.get_serializer(created_reviews, many=True)
        return Response(
            {
                "message": f"Successfully created {len(created_reviews)} review tasks.",
                "reviews": serializer.data
            },
            status=status.HTTP_201_CREATED
        )

    def get(self, request, *args, **kwargs):
        plan_id = kwargs.get("plan_id")

        if not plan_id:
            return Response({"detail": "plan_id is required in the URL."}, status=status.HTTP_400_BAD_REQUEST)

        queryset = self.get_queryset().filter(task__plan_validation_id=plan_id)

        if not queryset.exists():
            return Response({"message": "No reviews found for this plan."}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)