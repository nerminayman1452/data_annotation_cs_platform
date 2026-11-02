from collections import Counter
from django.db import transaction

from django.apps import apps
# from apps.image_annotation.models.base_models.base_task import TaskStatus, AnnotationStatus
# from apps.planning.models.base_config import BaseImagePlanConfig

class IAAStrategy:
    def __init__(self, task):
        self.task = task
        self.plan = task.plan
        self.batch = task.plan
        # self.plan = self._get_plan_for_task(self.plan_task)
        self.plan_config = self.plan.get_config() if self.plan else None

    # def _get_plan_for_task(self, plan_task):
    #     """Get the plan associated with the task's batch"""
    #     if not self.batch:
    #         return None
            
    #     # Try to find a plan for this batch
    #     plan_models = [
    #         'image_annotation.ImageClassificationPlan',
    #         'image_annotation.ObjectDetectionPlan',
    #         'image_annotation.PolygonPlan'
    #     ]
        
    #     for model_name in plan_models:
    #         try:
    #             model = apps.get_model(model_name)
    #             plan = model.objects.filter(batch=self.batch).first()
    #             if plan:
    #                 return plan
    #         except LookupError:
    #             continue
    #     return None

    def run(self):
        """Run IAA analysis based on plan configuration"""
        if not self.plan or not self.plan_config:
            return False

        # Get all final annotations for this task
        annotations = self.task.annotations.filter(
            status__in=AnnotationStatus.FINAL
        ).select_related('label_type_result')
        print(f"annotations: {annotations}" )

        required_annotators = self.plan_config.annotators_per_task or 1
        current_count = annotations.count()

        print(f"required_annotators: {required_annotators}" )
        print(f"current_count: {current_count}" )

        if current_count < required_annotators:
            return False

        print (f"check annotations: {annotations}" )

        return self._calculate_majority(annotations, required_annotators)

    def _calculate_majority(self, annotations, required_annotators):
        """Calculate majority based on annotation type and plan configuration"""
        votes = []
        vote_objects = {}  # Map from vote key to actual object

        # Process annotations based on their type
        for ann in annotations:
            vote_key = self._get_vote_key(ann)
            print(f"vote_key: {vote_key}" )
            if vote_key is None:
                continue

            votes.append(vote_key)
            vote_objects[vote_key] = {
                'object': ann.label_type_result or ann.custom_label,
                'annotation': ann
            }
            print(f"vote_objects: {vote_objects}" )
        # {"label_1": {"object": "label_1", "annotation": annotation_1}, "label_2": {"object": "label_2", "annotation": annotation_2}}


        if not votes:
            return False

        counter = Counter(votes)
        most_common = counter.most_common()
        top_choice, vote_count = most_common[0]

        # Calculate consensus based on plan configuration
        consensus_achieved = self._check_consensus_achieved(
            counter, most_common, required_annotators
        )
        print(f"consensus_achieved: {consensus_achieved}" )

        # Update task status based on consensus
        self._update_task_status(consensus_achieved, most_common, vote_objects)
        return consensus_achieved

    def _get_vote_key(self, annotation):
        """Get a unique key for each type of vote"""
        if annotation.label_type_result:
            return f"label_{annotation.label_type_result.id}"
        elif annotation.custom_label:
            return f"custom_{hash(annotation.custom_label.strip().lower())}"
        return None

    def _check_consensus_achieved(self, counter, most_common, required_annotators):
        """Check if consensus is achieved based on plan configuration"""
        if not most_common:
            return False

        top_choice, vote_count = most_common[0]
        print(f"top_choice: {top_choice}")
        print(f"vote_count: {vote_count}")
        
        # Calculate agreement percentage
        agreement_pct = (vote_count / required_annotators) * 100
        print(f"agreement_percentage: {agreement_pct}%")
        
        # Get acceptance_agreement from plan config (default to 0 if not set)
        acceptance_agreement = getattr(self.plan_config, 'acceptance_agreement', 0)
        print(f"required_acceptance_agreement: {acceptance_agreement}%")
        
        # Check if we meet the minimum acceptance_agreement threshold
        if acceptance_agreement and agreement_pct < acceptance_agreement:
            print(f"Consensus not reached: {agreement_pct}% is below required {acceptance_agreement}%")
            return False
            
        # Check for perfect agreement (all annotators agree)
        if vote_count == required_annotators:
            return True

        # Check for majority (more than 50%)
        if vote_count > (required_annotators / 2):
            return True

        # Check for tie (if there's a second item with same count)
        if len(most_common) > 1 and most_common[0][1] == most_common[1][1]:
            print("Consensus not reached: tie between top choices")
            return False

        # If we have a clear winner but not majority, check if it meets minimum threshold
        min_agreement = getattr(self.plan_config, 'min_agreement_percentage', None)
        if min_agreement:
            print(f"Checking against min_agreement_percentage: {min_agreement}%")
            return agreement_pct >= min_agreement

        print("Consensus not reached: no agreement criteria met")
        return False

    def _update_task_status(self, consensus_achieved, most_common, vote_objects):
        """Update task status based on consensus result"""
        with transaction.atomic():
            if consensus_achieved:
                top_choice, _ = most_common[0]
                vote_data = vote_objects[top_choice]
                
                self.task.task_status = TaskStatus.IAA_RESOLVED
                self.task.accepted_by = "IAA"
                
                # Set the winning annotation
                if isinstance(vote_data['object'], str):  # Custom label
                    self.task.final_custom_label = vote_data['object']
                    self.task.final_label_result = None
                else:  # LabelType instance
                    self.task.final_label_result = vote_data['object']
                    self.task.final_custom_label = None
                
                # Update annotation statuses
                self._update_annotation_statuses(most_common, vote_objects)
            else:
                self.task.task_status = TaskStatus.CONFLICT
                self.task.accepted_by = None
                self.task.final_label_result = None
                self.task.final_custom_label = None

            self.task.save()

    def _update_annotation_statuses(self, most_common, vote_objects):
        """Update statuses of annotations based on consensus"""
        winning_vote = most_common[0][0]
        
        for vote_key, data in vote_objects.items():
            annotation = data['annotation']
            if vote_key == winning_vote:
                annotation.status = AnnotationStatus.ACCEPTED
            else:
                annotation.status = AnnotationStatus.REJECTED
            annotation.save()

