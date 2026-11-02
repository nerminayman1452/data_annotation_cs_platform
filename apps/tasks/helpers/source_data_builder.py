import abc


class SourceDataBuilder(abc.ABC):
    @abc.abstractmethod
    def build(self, raw_unit, payload):
        pass


class TextSourceDataBuilder(SourceDataBuilder):
    def build(self, raw_unit, payload):
        return payload


class ImageSourceDataBuilder(SourceDataBuilder):
    def build(self, raw_unit, payload):
        # Original image file
        if payload is None:
            return {
                "file_url": raw_unit.file.url if raw_unit.file else "",
                "file_name": raw_unit.file.name if raw_unit.file else "",
            }

        return payload
