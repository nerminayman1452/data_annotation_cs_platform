from enum import Enum

from unused_scripts.structured_data import SegmentationStrategy


class SegmentationUnit(Enum):
    WORD = "word"
    SENTENCE = "sentence"
    PARAGRAPH = "paragraph"
    ARTICLE = "article"


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
