import abc


class SegmentationStrategy(abc.ABC):
    """Responsible ONLY for splitting content into units."""
    @abc.abstractmethod
    def segment(self, raw_content):
        pass


class StructuredStrategy(SegmentationStrategy):
    """
    Iterates over lists (JSON Arrays or CSV Rows).
    """

    def segment(self, raw_content) :
        iterable_data = raw_content if isinstance(raw_content, list) else [raw_content]

        for index, item in enumerate(iterable_data,start=1):
            # If item is a string (e.g. JSON list of strings), wrap it in dict
            # If item is a dict (CSV row), keep it as is.
            final_data = item if isinstance(item, dict) else {"text": item}

            yield {
                "data": final_data,
                "order": index
            }