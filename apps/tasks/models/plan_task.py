import json
from collections import Counter

from django.db import models

from apps.profile.models.profile import Profile
from apps.project_management.models.time_stamp import TimeStampedModel

class TaskStatus:
    PENDING = "PENDING"              # Waiting for annotators
    IAA_RESOLVED = "IAA_RESOLVED"    # Majority vote succeeded
    CONFLICT = "CONFLICT"            # No majority, needs manual adjudication
    MANUAL_REVIEWED = "MANUAL_REVIEWED"       # Adjudicator fixed it

    CHOICES = [
        (PENDING, "Pending"),
        (IAA_RESOLVED, "IAA Resolved"),
        (CONFLICT, "IAA Conflict / Needs Adjudication"),
        (MANUAL_REVIEWED, "Manually Reviewed"),
    ]


class BasePlanTask(TimeStampedModel):
    """
    Represents a single unit of work (e.g., one sentence, one image) within a Batch.
    It tracks the 'Final Result' (Consensus) derived from multiple annotators.
    """
    source_data = models.JSONField(verbose_name="Input Data", default=dict)
    finalized_result = models.JSONField(null=True, default=dict, blank=True)

    task_status = models.CharField(
        max_length=32, 
        choices=TaskStatus.CHOICES, 
        default=TaskStatus.PENDING,
        db_index=True # Index for faster filtering in dashboards
    )

    accepted_by = models.ForeignKey(
        Profile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_accepted_tasks"
    )
    accepted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    @property
    def export_task_result(self):
        """
        Returns all derived task information in one stable JSON payload.
        Does NOT mutate database.
        """
        comparison_key = self._get_comparison_key() or []
        annotation_list = self._get_valid_annotations()

        most_common_payload = {}
        if comparison_key and annotation_list:
            most_common_payload = self._calculate_most_common(annotation_list, comparison_key)

        return {
            "source_data": self.source_data or {},
            "annotations": annotation_list,
            "most_common": most_common_payload,
            "finalized_result": self.finalized_result,
        }

    # ----------------------------
    # 🔧 Internal Helpers
    # ----------------------------

    def _get_valid_annotations(self):
        return list(
            self.annotations.filter(status__in=["SUBMITTED", "ACCEPTED"])
            .values_list("annotated_data", flat=True)
        )

    def _get_comparison_key(self):
        plan = getattr(self, "plan", None)
        if plan and plan.annotation_type:
            return plan.annotation_type.comparison_key
        return None

    def _calculate_most_common(self, data_list, keys):
        """
        Calculates consensus per key.
        Returns: { key: most_common_value }
        """
        result = {}

        for key in keys:
            counter = Counter()
            objects = {}

            for data in data_list:
                value = data.get(key)
                if value is None:
                    continue

                converted = json.dumps(value, sort_keys=True)
                counter[converted] += 1

                if converted not in objects:
                    objects[converted] = value

            if counter:
                most_common_key, _ = counter.most_common(1)[0]
                result[key] = objects[most_common_key]

        return result

    #todo - need to be tested and reviewed
    # @property
    # def most_common(self):
    #     """
    #     Returns the most common annotation result as a tuple: (label_id, count).
    #     """
    #     counter = Counter()
    #     # Use .all() to iterate the QuerySet
    #     for annotation in self.annotations.all():
    #         # FIX: Use 'label_type_result_id' (Integer) instead of the object.
    #         # This prevents the "not JSON serializable" error and avoids extra DB queries.
    #         if annotation.label_type_result_id:
    #             counter[annotation.label_type_result_id] += 1
            
    #     if not counter:
    #         return None 
            
    #     return counter.most_common(1)[0]

    # @property
    # def most_common_majority_percentage(self):
    #     """
    #     Returns the percentage of annotators who agreed on the most common label.
    #     """
    #     # Use .count() for DB efficiency
    #     total_annotations = self.annotations.count()
        
    #     # Prevent DivisionByZeroError
    #     if total_annotations == 0:
    #         return 0.0

    #     most_common_result = self.most_common
    #     if not most_common_result:
    #         return 0.0
            
    #     # Unpack tuple (label_id, count)
    #     _, count = most_common_result
    #     return (count / total_annotations) * 100

    # def _get_comparison_key(self):
#     """
#     Determines which JSON key to compare based on the Plan's AnnotationType.
#     """
#     # 1. Access the child Plan object (e.g., ImagePlan)
#     plan = getattr(self, 'plan', None)
#     if not plan:
#         return None
#     annot_type_name = getattr(plan.annotation_type, 'name', '').lower()
#
#     TYPE_TO_KEY_MAPPING = {
#         'classification': 'label',  # annot_data = {'label': 'cat'}
#         'object detection': 'boxes',  # annot_data = {'boxes': [...]}
#         'polygons': 'points',  # annot_data = {'points': [...]}
#         'validation': 'label',  # annot_data = {'label': 'accepted'}
#     }
#
#     return TYPE_TO_KEY_MAPPING.get(annot_type_name)
