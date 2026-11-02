import csv
from datetime import timezone
import io
import json
from django.core.files.base import ContentFile


class ResultMigrator:
    """
    Responsible solely for exporting Task Results from the source plan
    and saving them as a new CSV Raw Data file in the new plan.
    """
    @staticmethod
    def migrate(source_plan, new_plan, data_model):
        """Migrates task results from source_plan to new_plan as a CSV Raw Data file."""
        if not data_model or not hasattr(source_plan, 'plan_tasks'):
            return

        # 1. Generate CSV Content
        csv_content = ResultMigrator._generate_csv(source_plan)
        if not csv_content:
            return

        # 2. Save as new Raw Data
        ResultMigrator._save_csv_as_raw_data(new_plan, data_model, csv_content)

    @staticmethod
    def _generate_csv(source_plan):
        """Generates a CSV string from plan tasks."""
        tasks = source_plan.plan_tasks.all().iterator()
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        headers = ['task_id', 'source_data', 'finalized_result', 'most_common_result', 'annotations','annotations_count']
        writer.writerow(headers)
        
        has_data = False
        for task in tasks:
            has_data = True
            result = task.export_task_result
            writer.writerow([
                task.id,
                json.dumps(result.get('source_data', {})),
                json.dumps(result.get('finalized_result', {})),
                json.dumps(result.get('most_common', {})),
                json.dumps(result.get('annotations', [])),
                len(result.get('annotations', []))
            ])
            
        if not has_data:
            return None
            
        return output.getvalue()

    @staticmethod
    def _save_csv_as_raw_data(new_plan, data_model, csv_content):
        """Saves the CSV content as a new Raw Data object linked to new_plan."""
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        file_name = f"tasks_results_{new_plan.id}_{timestamp}.csv"
        
        file_obj = ContentFile(csv_content.encode('utf-8'))
        
        new_raw_data = data_model(plan=new_plan, file_name=file_name)
        new_raw_data.file.save(file_name, file_obj, save=True)