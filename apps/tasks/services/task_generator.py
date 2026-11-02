from apps.tasks.helpers.data_segmentation_strategy import NoSegmentationStrategy
from apps.tasks.helpers.task_processor import ProcessorFactory


class PlanTaskGenerationService:
    """
    Unified Task Generator for Text, Image, CSV, XLSX, etc.
    """

    def __init__(self, plan, source_data_builder):
        self.plan = plan
        self.task_model = self.plan.get_task_model()
        self.builder = source_data_builder
        self.estimation_config = self.plan.get_estimation_config()
        self.measure_unit = self.estimation_config.measure_unit.title

    def generate(self):
        existing_ids = set(
            self.task_model.objects.filter(plan=self.plan)
            .values_list("plan_file_id", flat=True)
        )

        tasks = []

        for raw_file in self.plan.raw_data_files.exclude(id__in=existing_ids):

            loader, strategy = ProcessorFactory.get_components(
                raw_file.file.path,
                self.measure_unit,
            )
            if isinstance(strategy, NoSegmentationStrategy):
                content = None
            else:
                content = loader.load(raw_file.file.path)
            for payload in strategy.segment(content):
                source_data = self.builder.build(raw_file, payload)
                tasks.append(
                    self.task_model(
                        plan=self.plan,
                        plan_file=raw_file,
                        source_data=source_data,
                        finalized_result=None,
                    )
                )

        created_tasks = []
        if tasks:
            created_tasks = self.task_model.objects.bulk_create(tasks, batch_size=500)

        return created_tasks