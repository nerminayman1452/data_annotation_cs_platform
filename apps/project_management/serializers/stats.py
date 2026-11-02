import math
from decimal import Decimal

from apps.project_management.serializers.batch import BatchSerializer
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.project_management.models.batch import Batch
from apps.project_management.models.project import Project


class BatchPlanStatsSerializer(serializers.ModelSerializer):
    total = serializers.SerializerMethodField()
    average = serializers.SerializerMethodField()

    class Meta:
        model = Batch
        fields = ['id', 'name', 'total', 'average']

    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_total(self, batch):
        """Get total statistics for all plans in the batch"""
        all_plans = batch.get_all_plans()
        
        # Calculate totals from all plans
        total_units = sum(getattr(plan, 'total_units', 0) for plan in all_plans)
        actual_units = sum(getattr(plan, 'actual_units', 0) for plan in all_plans)
        total_estimated_budget = sum(float(getattr(plan, 'total_estimated_budget', 0)) for plan in all_plans)
        
        # Calculate duration
        duration_days = sum(getattr(plan, 'duration_days', 0) for plan in all_plans)
        
        # Calculate progress
        progress = sum(getattr(plan, 'progress', 0) for plan in all_plans)
        
        # Calculate workers and costs
        workers = sum(getattr(plan, 'workers', 0) for plan in all_plans)
        cost_per_unit = sum(float(getattr(plan, 'cost_per_unit', 0)) for plan in all_plans)
        
        # Calculate standard and rates
        standard = sum(getattr(plan, 'standard', 0) for plan in all_plans)
        rates = sum(float(getattr(plan, 'rates', 0)) for plan in all_plans)
        
        # Calculate efforts and task_cost
        efforts = sum(float(getattr(plan, 'efforts', 0)) for plan in all_plans)
        task_cost = sum(float(getattr(plan, 'task_cost', 0)) for plan in all_plans)
        
        # Calculate weight
        weight = sum(float(getattr(plan, 'weight', 0)) for plan in all_plans)
        weight_times_progress = sum(float(getattr(plan, 'weight_times_progress', 0)) for plan in all_plans)
        
        # Get batch estimates and actuals if available
        estimates = getattr(batch, 'estimates', None)
        actuals = getattr(batch, 'actuals', None)
        
        return {
            'standard': standard,
            'workers': workers,
            'rates': rates,
            'actual_progress': progress,
            'efforts': efforts,
            'task_cost': task_cost,
            'duration_days': duration_days,
            'duration_weeks': math.ceil(duration_days / 5) if duration_days > 0 else 0,
            'weight': weight,
            'weight_times_progress': weight_times_progress,
            'cost_per_unit': cost_per_unit,
            'start_date': getattr(estimates, 'start_date', None) if estimates else None,
            'end_date': getattr(estimates, 'end_date', None) if estimates else None,
            'total_units': total_units,
            'total_estimated_budget': total_estimated_budget,
            'actual_units': actual_units,
        }

    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_average(self, batch):
        """Get average statistics for all plans in the batch"""
        all_plans = batch.get_all_plans()
        plans_count = len(all_plans) or 1
        
        # Calculate totals first
        totals = self.get_total(batch)
        
        # Calculate averages
        return {
            'standard': totals['standard'] / plans_count,
            'workers': totals['workers'] / plans_count,
            'rates': totals['rates'] / plans_count,
            'actual_progress': totals['actual_progress'] / plans_count,
            'efforts': totals['efforts'] / plans_count,
            'task_cost': totals['task_cost'] / plans_count,
            'duration_days': totals['duration_days'] // plans_count,
            'duration_weeks': math.ceil((totals['duration_days'] / 5) / plans_count) if totals['duration_days'] > 0 else 0,
            'weight': totals['weight'] / plans_count,
            'weight_times_progress': totals['weight_times_progress'] / plans_count,
            'cost_per_unit': totals['cost_per_unit'] / plans_count,
            'start_date': totals['start_date'],
            'end_date': totals['end_date'],
            'total_units': totals['total_units'] / plans_count,
            'total_estimated_budget': totals['total_estimated_budget'] / plans_count,
            'actual_units': totals['actual_units'] / plans_count,
        }


class ProjectBatchStatsSerializer(serializers.ModelSerializer):
    total = serializers.SerializerMethodField()
    average = serializers.SerializerMethodField()
    batches = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = ['id', 'project_name', 'total', 'average', 'batches']

    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_total(self, project):
        """Get total statistics for the project using project-level aggregated fields."""

        # Prefer using pre-computed/aggregated fields on the Project model.
        estimates = getattr(project, 'estimates', None)
        actuals = getattr(project, 'actuals', None)

        total_units = getattr(estimates, 'total_units', 0) if estimates else 0
        actual_units = getattr(actuals, 'total_units', 0) if actuals else 0

        duration_days = getattr(estimates, 'duration_days', 0) if estimates else 0
        duration_weeks = getattr(estimates, 'duration_weeks', 0) if estimates else 0

        progress = getattr(actuals, 'progress', 0) if actuals else 0
        weight = float(getattr(project, 'weight', 0))

        weight_times_progress = float(getattr(actuals, 'weight_times_progress', 0) if actuals else 0)

        task_effort_per_day = float(getattr(estimates, 'daily_efforts', 0) if estimates else 0)
        tasks_per_day = float(getattr(estimates, 'tasks_per_day', 0) if estimates else 0)

        effort_days = float(getattr(estimates, 'total_efforts', 0) if estimates else 0)
        time_elapsed_percentage = float(getattr(actuals, 'time_elapsed_percent', 0) if actuals else 0)

        start_date = getattr(estimates, 'start_date', None) if estimates else None
        end_date = getattr(estimates, 'end_date', None) if estimates else None

        return {
            'duration_days': duration_days,
            'duration_weeks': duration_weeks,
            'total_units': total_units,
            'task_effort_per_day': task_effort_per_day,
            'tasks_per_day': tasks_per_day,
            'effort_days': effort_days,
            'progress': progress,
            'weight': weight,
            # 'in_progress_weight_times_progress': in_progress_weight_times_progress,
            'weight_times_progress': weight_times_progress,
            'time_elapsed_percentage': time_elapsed_percentage,
            'start_date': start_date,
            'end_date': end_date,
        }

    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_average(self, project):
        """Get average statistics for all batches in the project"""
        totals = self.get_total(project)
        batches_count = project.batches.count() or 1
        
        return {
            'duration_days': totals['duration_days'] // batches_count,
            'duration_weeks': totals['duration_weeks'] / batches_count,
            'total_units': totals['total_units'] / batches_count,
            'task_effort_per_day': totals['task_effort_per_day'] / batches_count,
            'tasks_per_day': totals['tasks_per_day'] / batches_count,
            'effort_days': totals['effort_days'] / batches_count,
            'progress': totals['progress'] / batches_count,
            'weight': totals['weight'] / batches_count,
            # 'in_progress_weight_times_progress': totals['in_progress_weight_times_progress'] / batches_count,
            'weight_times_progress': totals['weight_times_progress'] / batches_count,
            'time_elapsed_percentage': totals['time_elapsed_percentage'] / batches_count,
            'start_date': totals['start_date'],
            'end_date': totals['end_date'],
        }

    def get_batches(self, project):
        """Get all batches with their stats for the project"""
        batches = project.batches.all()
        return BatchSerializer(batches, many=True, context=self.context).data
