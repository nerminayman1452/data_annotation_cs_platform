import calendar
from datetime import date, datetime
from decimal import Decimal

from apps.project_management.models.batch import Batch


class GraphHandler:
    """
    Handles graph data generation for plans, batches, and projects
    in the crowdsourcing platform.
    """

    def count_covered_days(self, start_date, end_date):
        """
        Calculate the number of days between start_date and end_date (inclusive).
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            int: Number of days
        """
        if not start_date or not end_date:
            return 0
        return (end_date - start_date).days + 1

    def covered_days_every_month(self, start_date, days_covered, daily_cost, total_cost=0):
        """
        Calculate cumulative cost for each month covered by the plan.
        
        Args:
            start_date: Plan start date
            days_covered: Total number of days in the plan
            daily_cost: Cost per day
            total_cost: Starting total cost (for estimated calculations)
            
        Returns:
            dict: Monthly cumulative cost data
        """
        if not start_date or days_covered <= 0 or daily_cost <= 0:
            return {}
            
        current_year = start_date.year
        current_month = start_date.month
        data = {}
        
        while days_covered > 0:
            # Calculate days left in current month
            days_in_month = calendar.monthrange(current_year, current_month)[1]
            days_left_in_month = days_in_month - start_date.day + 1
            cost_days = min(days_left_in_month, days_covered)
            
            # Calculate cumulative cost for this month
            total_cost += (cost_days * float(daily_cost))
            data[f"{calendar.month_name[current_month]} {current_year}"] = round(total_cost, 2)
            
            # Move to next month
            days_covered -= cost_days
            current_month += 1
            if current_month > 12:
                current_month = 1
                current_year += 1
            start_date = date(current_year, current_month, 1)
            
        return data

    def normal_planned_cost(self, start_date, days_covered, daily_cost):
        """
        Calculate the normal/planned cost trajectory.
        
        Args:
            start_date: Plan start date
            days_covered: Total duration in days
            daily_cost: Expected daily cost
            
        Returns:
            dict: Monthly planned cumulative cost
        """
        return self.covered_days_every_month(start_date, days_covered, daily_cost)

    def actual_cost_so_far(self, start_date, days_passed, actual_daily_cost):
        """
        Calculate the actual cost incurred so far.
        
        Args:
            start_date: Plan start date
            days_passed: Number of days actually passed
            actual_daily_cost: Actual daily cost incurred
            
        Returns:
            dict: Monthly actual cumulative cost
        """
        return self.covered_days_every_month(start_date, days_passed, actual_daily_cost)

    def estimated_future_cost(self, days_left, actual_daily_cost, start_cost):
        """
        Calculate estimated future cost based on current trends.
        
        Args:
            days_left: Number of days remaining
            actual_daily_cost: Current actual daily cost rate
            start_cost: Starting point (current actual cost)
            
        Returns:
            dict: Monthly estimated cumulative cost
        """
        if days_left <= 0:
            return {}
        
        start_date = datetime.now().date()
        return self.covered_days_every_month(start_date, days_left, actual_daily_cost, float(start_cost))

    def calculate_days_passed(self, start_date, end_date):
        """
        Calculate how many days have passed from start_date until now or end_date.
        
        Args:
            start_date: Plan start date
            end_date: Plan end date
            
        Returns:
            int: Number of days passed
        """
        if not start_date:
            return 0
            
        today = datetime.now().date()
        
        if end_date and end_date <= today:
            # Plan has ended
            return self.count_covered_days(start_date, end_date)
        else:
            # Plan is ongoing or hasn't started yet
            if today >= start_date:
                return self.count_covered_days(start_date, today)
            else:
                # Plan hasn't started yet
                return 0

    def get_graph_labels(self, normal, actual, estimated):
        """
        Get sorted list of all unique month labels from all datasets.
        
        Args:
            normal: Planned cost data
            actual: Actual cost data
            estimated: Estimated cost data
            
        Returns:
            list: Sorted month labels
        """
        all_keys = set(normal.keys()) | set(actual.keys()) | set(estimated.keys())
        
        def parse_month_year(month_str):
            try:
                return datetime.strptime(month_str, '%B %Y')
            except ValueError:
                return datetime.now()
        
        return sorted(all_keys, key=parse_month_year)

    def get_line_chart_data(self, start_date, actual_start_date, days_covered, days_passed, 
                          planned_daily_cost, actual_daily_cost):
        """
        Generate complete line chart data for cost tracking.
        
        Args:
            start_date: Planned start date
            actual_start_date: Actual start date (usually same as start_date)
            days_covered: Total planned duration
            days_passed: Days actually passed
            planned_daily_cost: Planned daily cost
            actual_daily_cost: Actual daily cost
            
        Returns:
            dict: Complete chart data with all three lines
        """
        # Calculate planned cost trajectory
        planned = self.normal_planned_cost(start_date, days_covered, planned_daily_cost)
        
        # Calculate actual cost so far
        actual = self.actual_cost_so_far(actual_start_date, days_passed, actual_daily_cost)
        
        # Calculate estimated future cost
        days_left = max(0, days_covered - days_passed)
        current_actual_cost = list(actual.values())[-1] if actual else 0
        estimated = self.estimated_future_cost(days_left, actual_daily_cost, current_actual_cost)
        
        # Get the final values for each cost type
        final_planned_cost = list(planned.values())[-1] if planned else 0
        final_actual_cost = list(actual.values())[-1] if actual else 0
        final_estimated_cost = list(estimated.values())[-1] if estimated else 0
        
        return {
            'labels': [final_planned_cost, final_actual_cost, final_estimated_cost],
            'planned_cost': final_planned_cost,
            'actual_cost': final_actual_cost,
            'estimated_cost': final_estimated_cost,
        }

    def plan_line_chart_data(self, plan):
        """
        Generate line chart data for a specific plan.
        
        Args:
            plan: Plan object (TextPlan, ImagePlan, AudioPlan)
            
        Returns:
            dict: Chart data for the plan
        """
        # Get estimation config
        estimation_config = getattr(plan, 'estimation_config', None)
        cost_config = getattr(plan, 'cost_config', None)
        
        if not estimation_config or not cost_config:
            return {'error': 'Plan missing configuration data'}
        
        start_date = estimation_config.start_date
        
        # Use duration_days from plan response mixin if available, otherwise fall back to duration
        days_covered = getattr(plan, 'duration_days', 0)
        if days_covered == 0:
            # Fallback to duration from estimation_config
            days_covered = estimation_config.duration or 0
        
        # Calculate days passed
        days_passed = self.calculate_days_passed(start_date, None)
        
        # Calculate planned daily cost from total budget
        total_estimated_budget = getattr(cost_config, 'total_estimated_budget', 0)
        planned_daily_cost = 0
        
        if total_estimated_budget > 0 and days_covered > 0:
            planned_daily_cost = total_estimated_budget / days_covered
        else:
            # Fallback to cost_per_unit * total_units / days_covered
            cost_per_unit = getattr(cost_config, 'cost_per_unit', 0) or 0
            total_units = getattr(estimation_config, 'total_units', 0)
            if cost_per_unit > 0 and total_units > 0 and days_covered > 0:
                planned_daily_cost = (cost_per_unit * total_units) / days_covered
        
        # Calculate actual daily cost based on progress
        actual_daily_cost = self.calculate_actual_daily_cost(plan)
        
        # Get plan type for labels
        plan_type = getattr(plan, 'actual_plan_detail', f"{plan.__class__.__name__.replace('Plan', '').upper()} Plan")
        
        # If we still have zero values, return the total budget directly as planned cost
        if planned_daily_cost == 0 and total_estimated_budget > 0:
            return {
                'labels': [getattr(plan, 'name',None)],
                'planned_cost': float(total_estimated_budget),
                'actual_cost': 0.0,
                'estimated_cost': 0.0,
            }
        
        # Get the chart data
        chart_data = self.get_line_chart_data(
            start_date=start_date,
            actual_start_date=start_date,
            days_covered=days_covered,
            days_passed=days_passed,
            planned_daily_cost=planned_daily_cost,
            actual_daily_cost=actual_daily_cost
        )
        
        # Override labels with plan type
        chart_data['labels'] = [getattr(plan, 'name',None)]
        
        return chart_data

    def batch_line_chart_data(self, batch):
        """
        Generate line chart data for a batch.
        
        Args:
            batch: Batch object
            
        Returns:
            dict: Chart data for the batch
        """
        # Get batch estimates
        estimates = getattr(batch, 'estimates', None)
        if not estimates:
            return {'error': 'Batch missing estimates data'}
        
        start_date = estimates.start_date
        end_date = estimates.end_date
        days_covered = self.count_covered_days(start_date, end_date) if start_date and end_date else 0
        days_passed = self.calculate_days_passed(start_date, end_date)
        
        # Calculate daily costs from batch data
        planned_daily_cost = self.calculate_batch_daily_cost(batch, planned=True)
        actual_daily_cost = self.calculate_batch_daily_cost(batch, planned=False)
        
        return self.get_line_chart_data(
            start_date=start_date,
            actual_start_date=start_date,
            days_covered=days_covered,
            days_passed=days_passed,
            planned_daily_cost=planned_daily_cost,
            actual_daily_cost=actual_daily_cost
        )

    def calculate_actual_daily_cost(self, plan):
        """
        Calculate actual daily cost for a plan based on current progress.
        
        Args:
            plan: Plan object
            
        Returns:
            float: Actual daily cost
        """
        # Get actual progress and cost
        actual_units = getattr(plan, 'actual_units', 0)
        total_estimated_budget = getattr(plan, 'total_estimated_budget', 0)
        total_units = getattr(plan, 'total_units', 0)
        progress = getattr(plan, 'progress', 0)
        
        # If there's no progress, actual daily cost should be 0
        if progress <= 0 or actual_units <= 0:
            return 0
        
        # Calculate actual cost based on progress
        if total_estimated_budget > 0:
            actual_cost_spent = total_estimated_budget * (progress / 100)
            
            # Calculate days passed
            estimation_config = getattr(plan, 'estimation_config', None)
            if estimation_config and estimation_config.start_date:
                days_passed = self.calculate_days_passed(estimation_config.start_date, None)
                if days_passed > 0:
                    return actual_cost_spent / days_passed
        
        # Fallback to planned cost if there's some progress but we can't calculate properly
        cost_config = getattr(plan, 'cost_config', None)
        return cost_config.cost_per_unit if cost_config else 0

    def calculate_batch_daily_cost(self, batch, planned=True):
        """
        Calculate daily cost for a batch.
        
        Args:
            batch: Batch object
            planned: Whether to calculate planned or actual daily cost
            
        Returns:
            float: Daily cost
        """
        if planned:
            # Use estimates
            estimates = getattr(batch, 'estimates', None)
            if estimates and estimates.total_efforts and estimates.start_date and estimates.end_date:
                days = self.count_covered_days(estimates.start_date, estimates.end_date)
                if days > 0:
                    return float(estimates.total_cost) / days
        else:
            # Use actuals
            actuals = getattr(batch, 'actuals', None)
            estimates = getattr(batch, 'estimates', None)
            if actuals and estimates and estimates.start_date:
                days_passed = self.calculate_days_passed(estimates.start_date, None)
                if days_passed > 0:
                    return float(actuals.total_cost) / days_passed
        
        return 0
