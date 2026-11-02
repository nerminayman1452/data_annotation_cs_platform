
import copy
from apps.project_management.models.text_plan import TextPlan, TextPlanRawData
from apps.project_management.models.image_plan import ImagePlan, ImagePlanRawData
from apps.project_management.helpers.config_cloner import ConfigCloner
from apps.project_management.helpers.raw_data_cloner import RawDataCloner
from apps.project_management.helpers.result_migrator import ResultMigrator

class PlanCloner:
    """
    Facade Service.
    Orchestrates the cloning process by delegating to specialized cloners.
    """
    
    # Registry: Maps Plan Model Class -> Data Model Class
    DATA_MODEL_MAP = {
        TextPlan: TextPlanRawData,
        ImagePlan: ImagePlanRawData,
        # AudioPlan: AudioPlanRawData,
    }

    @classmethod
    def clone_plan(cls, source_plan, target_batch, name_prefix="", reuse_data=False, reuse_results=False):
        """
        Main entry point. Creates a deep copy of source_plan into target_batch.
        """

        # 1. Clone the Plan Shell
        new_plan = cls._create_plan_shell(source_plan, target_batch, name_prefix)

        # 2. Delegate Config Cloning
        ConfigCloner.clone(source_plan, new_plan)

        # # 3. Resolve Data Model
        # data_model = cls.DATA_MODEL_MAP.get(type(source_plan))

        # 4. Delegate Data Reuse
        if reuse_data:
            cls._clone_raw_data(source_plan, new_plan)

        # 5. Delegate Result Migration
        if reuse_results:
            cls._clone_results_as_raw_data(source_plan, new_plan)

        return new_plan

    @staticmethod
    def _create_plan_shell(source_plan, target_batch, name_prefix):
        """
        Creates a new Plan instance copying basic fields from source_plan.
        """
        new_plan = copy.copy(source_plan)
        new_plan.id = None
        new_plan.pk = None
        new_plan.batch = target_batch
        new_plan.name = f"{name_prefix}{source_plan.name}"
        new_plan.status = 'pending'
        if hasattr(new_plan, 'progress'):
            new_plan.progress = 0
        new_plan.save()
        return new_plan

    @staticmethod
    def _clone_raw_data(source_plan, new_plan):
        """ Clones Raw Data records from source_plan to new_plan. """
        data_model = PlanCloner.DATA_MODEL_MAP.get(type(source_plan))
        return RawDataCloner.clone(source_plan, new_plan, data_model)

    @staticmethod
    def _clone_results_as_raw_data(source_plan, new_plan):
        """ Migrates Task Results from source_plan to new_plan as a new Raw Data file. """
        data_model = PlanCloner.DATA_MODEL_MAP.get(type(source_plan))
        return ResultMigrator.migrate(source_plan, new_plan, data_model)



