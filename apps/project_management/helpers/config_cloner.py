import copy
import csv
import io
import json
from django.core.files.base import ContentFile
from django.utils import timezone

from apps.project_management.models.text_plan import TextPlan
from apps.project_management.models.image_plan import ImagePlan


class ConfigCloner:
    """
    Responsible solely for cloning configuration, costs, and estimation settings.
    """
    @staticmethod
    def clone(source_plan, new_plan):
        ConfigCloner._clone_main_config(source_plan, new_plan)
        ConfigCloner._clone_cost(source_plan, new_plan)
        ConfigCloner._clone_estimation(source_plan, new_plan)

    @staticmethod
    def _clone_main_config(source_plan, new_plan):
        if not hasattr(source_plan, 'config'):
            return

        old_config = source_plan.config
        new_config = copy.copy(old_config)
        new_config.id = None
        new_config.plan = new_plan
        new_config.save()

        # Handle Polymorphic ManyToMany fields
        if isinstance(source_plan, TextPlan):
            ConfigCloner._copy_m2m(old_config, new_config, [
                'allowed_labels', 'allowed_errors', 
                'allowed_sentence_types', 'allowed_validation_types'
            ])
        elif isinstance(source_plan, ImagePlan):
            ConfigCloner._copy_m2m(old_config, new_config, [
                'classification_labels', 'detection_labels', 'polygon_labels'
            ])

    @staticmethod
    def _copy_m2m(source_obj, target_obj, field_names):
        for field in field_names:
            if hasattr(target_obj, field):
                getattr(target_obj, field).set(getattr(source_obj, field).all())

    @staticmethod
    def _clone_cost(source_plan, new_plan):
        if hasattr(source_plan, 'cost_config'):
            new_cost = copy.copy(source_plan.cost_config)
            new_cost.id = None
            new_cost.plan = new_plan
            new_cost.is_approved = False
            new_cost.approved_at = None
            new_cost.save()

    @staticmethod
    def _clone_estimation(source_plan, new_plan):
        if hasattr(source_plan, 'estimation_config'):
            new_est = copy.copy(source_plan.estimation_config)
            new_est.id = None
            new_est.plan = new_plan
            new_est.save()