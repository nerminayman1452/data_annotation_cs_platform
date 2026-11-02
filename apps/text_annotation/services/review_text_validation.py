import random
from django.db import transaction
from apps.project_management.models.plan_members import PlanMember
# from apps.text_annotation.models.plan_text_validation import TextValidationPlan
from apps.text_annotation.models.review_text_validation import ReviewTextValidationResult
from apps.text_annotation.models.task_text_validation import TextValidationTaskResult


class ReviewTextValidationGenerator:
    def create_reviews_to_task(self, task):
        """
        Assign multiple reviewers to a task based on the plan config.
        Avoids assigning the same reviewer more than once.
        """
        plan = task.plan.plan_validation_conf_id
        required_reviewers = plan.reviewers_per_task
        batch = task.plan
        all_reviewers = PlanMember.objects.filter(batch=batch, user_role='Reviewer')
        assigned_reviewer_ids = ReviewTextValidationResult.objects.filter(task=task).values_list('reviewer_id',
                                                                                                 flat=True)
        available_reviewers = all_reviewers.exclude(id__in=assigned_reviewer_ids)
        if available_reviewers.count() == 0:
            raise ValueError("No unassigned reviewers available for this task.")
        selected_reviewers = random.sample(
            list(available_reviewers),
            min(required_reviewers, available_reviewers.count())
        )
        created_reviews = []
        with transaction.atomic():
            for reviewer in selected_reviewers:
                review = ReviewTextValidationResult.objects.create(
                    reviewer=reviewer,
                    task=task,
                    role='reviewer',
                    status='in_progress',
                    is_accepted=True
                )
                created_reviews.append(review)
        return created_reviews

    # def create_reviews_to_plan_tasks(self,plan_id):
    #     plan = TextValidationPlan.objects.get(id=plan_id)
    #     tasks = TextValidationTaskResult.objects.filter(plan_validation=plan)
    #     all_reviews = []
    #     for task in tasks:
    #         reviews = self.create_reviews_to_task(task)
    #         all_reviews.append(reviews)
    #
    #     return all_reviews
