import copy
import io
from django.db import transaction
from django.core.files.base import ContentFile
from django.utils import timezone
from datetime import datetime
import csv
import json

# Import Plan Models and Data Models
from apps.project_management.models.text_plan import TextPlan, TextPlanRawData
from apps.project_management.models.image_plan import ImagePlan, ImagePlanRawData
# from apps.project_management.models.audio_plan import AudioPlan, AudioPlanRawData

class PlanCloner:
    """
    Helper service to clone Plans (Text, Image, Audio), their Configs, Data, and Results.
    """

    # Registry: Maps Plan Model Class -> Data Model Class
    DATA_MODEL_MAP = {
        TextPlan: TextPlanRawData,
        ImagePlan: ImagePlanRawData,
        # AudioPlan: AudioPlanRawData,
    }

    @staticmethod
    def clone_plan(source_plan, target_batch, name_prefix="", reuse_data=False, reuse_results=False):
        """
        Main entry point. Creates a deep copy of source_plan into target_batch.
        """
        # 1. Clone Main Plan Object
        # We use copy.copy to duplicate the python object, then reset DB identifiers
        new_plan = copy.copy(source_plan)
        new_plan.id = None
        new_plan.pk = None
        new_plan.batch = target_batch
        new_plan.name = f"{name_prefix}{source_plan.name}"
        new_plan.status = 'pending'
        
        # Reset progress metrics
        if hasattr(new_plan, 'progress'): new_plan.progress = 0
        
        new_plan.save()

        # 2. Clone Child Configs (Polymorphic)
        PlanCloner._clone_config(source_plan, new_plan)
        PlanCloner._clone_cost(source_plan, new_plan)
        PlanCloner._clone_estimation(source_plan, new_plan)

        # 3. Reuse Data (Raw Files)
        if reuse_data:
            PlanCloner._clone_raw_data(source_plan, new_plan)

        # 4. Reuse Results (Annotations)
        if reuse_results:
            PlanCloner._clone_results_as_raw_data(source_plan, new_plan)

        return new_plan

    @staticmethod
    def _clone_config(source_plan, new_plan):
        """
        Clones the OneToOne config and handles ManyToMany fields manually.
        """
        if not hasattr(source_plan, 'config'): 
            return
        
        old_config = source_plan.config
        new_config = copy.copy(old_config)
        new_config.id = None
        new_config.plan = new_plan
        new_config.save()

        # --- Polymorphic M2M Handling ---
        
        # 1. TEXT PLAN
        if isinstance(source_plan, TextPlan):
            # We use checks to ensure safety even if model fields change later
            if hasattr(new_config, 'allowed_labels'):
                new_config.allowed_labels.set(old_config.allowed_labels.all())
            if hasattr(new_config, 'allowed_errors'):
                new_config.allowed_errors.set(old_config.allowed_errors.all())
            if hasattr(new_config, 'allowed_sentence_types'):
                new_config.allowed_sentence_types.set(old_config.allowed_sentence_types.all())
            if hasattr(new_config, 'allowed_validation_types'):
                new_config.allowed_validation_types.set(old_config.allowed_validation_types.all())

        # 2. IMAGE PLAN
        elif isinstance(source_plan, ImagePlan):
            if hasattr(new_config, 'classification_labels'):
                new_config.classification_labels.set(old_config.classification_labels.all())
            if hasattr(new_config, 'detection_labels'):
                new_config.detection_labels.set(old_config.detection_labels.all())
            if hasattr(new_config, 'polygon_labels'):
                new_config.polygon_labels.set(old_config.polygon_labels.all())

    @staticmethod
    def _clone_cost(source_plan, new_plan):
        if not hasattr(source_plan, 'cost_config'): return
        
        new_cost = copy.copy(source_plan.cost_config)
        new_cost.id = None
        new_cost.plan = new_plan
        # Reset financial approvals
        new_cost.is_approved = False 
        new_cost.approved_at = None
        new_cost.save()

    @staticmethod
    def _clone_estimation(source_plan, new_plan):
        if not hasattr(source_plan, 'estimation_config'): return
        
        new_est = copy.copy(source_plan.estimation_config)
        new_est.id = None
        new_est.plan = new_plan
        new_est.save()

    @staticmethod
    def _clone_raw_data(source_plan, new_plan):
        """
        Clones raw data records safely.
        """
        # 1. Identify which Data Model to use (TextPlanRawData, ImagePlanRawData, etc.)
        plan_class = type(source_plan)
        DataModel = PlanCloner.DATA_MODEL_MAP.get(plan_class)

        if not DataModel:
            return # Should we log a warning? 

        # 2. Query data directly using the source plan ID
        # This avoids relying on 'related_name' which might differ between models.
        source_data_qs = DataModel.objects.filter(plan=source_plan)
        
        # 3. Create copies in memory
        new_data_objects = []
        for raw_obj in source_data_qs:
            # Create a shallow copy of the model instance
            raw_copy = copy.copy(raw_obj)
            raw_copy.id = None
            raw_copy.pk = None
            raw_copy.plan = new_plan
            
            # NOTE: raw_copy.file still points to the same S3/Local path.
            # This is efficient (Reuse) and does not duplicate the physical file.
            
            new_data_objects.append(raw_copy)
        
        # 4. Bulk write to DB
        if new_data_objects:
            DataModel.objects.bulk_create(new_data_objects)

    @staticmethod
    def _clone_results_as_raw_data(source_plan, new_plan):
        """
        Exports all task results from source_plan into a single CSV file
        and saves it as a new RawData object for new_plan.
        """
        # 1. Identify Data Model
        DataModel = PlanCloner.DATA_MODEL_MAP.get(type(new_plan))
        if not DataModel:
            return

        # 2. Get Tasks (Use 'plan_tasks' related_name defined in Task models)
        if not hasattr(source_plan, 'plan_tasks'):
            return

        # Use iterator() to handle large datasets efficiently
        tasks = source_plan.plan_tasks.all().iterator()

        # 3. Create CSV in memory
        import io  # Import here to ensure it's in scope
        csv_buffer = io.StringIO()
        csv_writer = csv.writer(csv_buffer)
        
        # Headers
        csv_writer.writerow([
            'task_id', 
            'source_data', 
            'finalized_result', 
            'most_common_result', 
            'annotations'
        ])
        
        has_data = False
        for task in tasks:
            has_data = True
            # Get the calculated export payload
            result = task.export_task_result
            
            # Write row using json.dumps to ensure valid JSON format in CSV columns
            csv_writer.writerow([
                task.id,
                json.dumps(result.get('source_data', {})),
                json.dumps(result.get('finalized_result', {})),
                json.dumps(result.get('most_common', {})),
                json.dumps(result.get('annotations', []))
            ])

        # If no tasks existed, do not create an empty file
        if not has_data:
            csv_buffer.close()
            return

        # 4. Save to new Raw Data Model
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        file_name = f"exported_results_{source_plan.id}_{timestamp}.csv"
        
        # Convert buffer to ContentFile
        file_content = ContentFile(csv_buffer.getvalue().encode('utf-8'))
        
        # Create instance and save file
        # Note: We rely on the model's 'file' field default storage logic
        new_raw_data = DataModel(plan=new_plan, file_name=file_name)
        new_raw_data.file.save(file_name, file_content, save=True)
        
        csv_buffer.close()
