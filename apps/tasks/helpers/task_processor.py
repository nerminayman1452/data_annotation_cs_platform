import os

from apps.tasks.helpers.data_segmentation_strategy import NoSegmentationStrategy, StructuredStrategy, SegmentationUnit, \
    UnstructuredStrategy
from apps.tasks.helpers.file_loader import FileLoader


class ProcessorFactory:
    """
    Decides which Strategy to use.
    The FileLoader itself orchestrates file-type handling.
    """

    STRUCTURED_EXTENSIONS = {'json', 'csv', 'tsv', 'xml', 'xlsx'}
    IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}

    @staticmethod
    def get_components(file_path: str, measure_unit: str):
        ext = os.path.splitext(file_path)[1].lower().lstrip(".")
        loader = FileLoader()
        if ext in ProcessorFactory.STRUCTURED_EXTENSIONS:
            return loader, StructuredStrategy()
        if ext in ProcessorFactory.IMAGE_EXTENSIONS:
            return loader, NoSegmentationStrategy()

        try:
            unit = SegmentationUnit(measure_unit.lower())
        except Exception:
            unit = SegmentationUnit.ARTICLE

        return loader, UnstructuredStrategy(unit)
