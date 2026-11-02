import abc
from enum import Enum

class SegmentationUnit(Enum):
    WORD = "word"
    SENTENCE = "sentence"
    PARAGRAPH = "paragraph"
    ARTICLE = "article"

class SegmentationStrategy(abc.ABC):
    """Responsible ONLY for splitting content into units."""
    @abc.abstractmethod
    def segment(self, raw_content):
        pass

class NoSegmentationStrategy(SegmentationStrategy):
    """One file → one task"""
    def segment(self, raw_content):
        yield None

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

class UnstructuredStrategy(SegmentationStrategy):
    """
    Splits text based on the Measure Unit (Sentence, Paragraph, etc.)
    """

    def __init__(self, unit: SegmentationUnit):
        self.unit = unit

    def segment(self, raw_content: str):
        handlers = {
            SegmentationUnit.ARTICLE: self._segment_article,
            SegmentationUnit.PARAGRAPH: self._segment_paragraph,
            SegmentationUnit.SENTENCE: self._segment_sentence,
            SegmentationUnit.WORD: self._segment_word,
        }
        segments = handlers[self.unit](raw_content)

        for index, text_segment in enumerate(segments, start=1):
            yield {
                "data": {"text": text_segment},
                "order": index
            }

    def _segment_article(self, text: str):
        return [text]

    def _segment_paragraph(self, text: str):
        return [p.strip() for p in text.split("\n\n") if p.strip()]

    def _segment_sentence(self, text: str):
        normalized = text.replace("?", ".").replace("!", ".")
        return [s.strip() for s in normalized.split(".") if s.strip()]

    def _segment_word(self, text: str):
        return text.split()


