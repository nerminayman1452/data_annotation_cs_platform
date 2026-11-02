import codecs
import os
import re

from django.conf import settings
from django.core.exceptions import ValidationError

from apps.project_management.models.batch import Batch
# from apps.project_management.models.batch import Batchfrom apps.project_management.models.text_batch_data import TextBatchData
from apps.text_annotation.services.file_reader import FileReader
from apps.text_annotation.services.file_writer import FileWriter
# from apps.text_annotation.models.plan_text_segmentation import TextSegmentationPlan
from apps.text_annotation.models.task_text_segmentation import TextSegmentationTaskResult


class SegmentationProcessor:
    def __init__(self, plan_id, batch_id):
        self.segmentation_plan = TextSegmentationPlan.objects.filter(id=plan_id).first()
        self.splitter = self.get_splitter(self.segmentation_plan.text_splitter_id.splitter)
        print(f"Decoded splitter repr: {repr(self.splitter)}")

        self.batch_data_list = TextBatchData.objects.filter(batch=batch_id, result__isnull=True)
        self.batch = Batch.objects.get(id=batch_id)
        self.file_writer = FileWriter()
        self.file_reader = FileReader()

    def get_splitter(self, splitter):
        splitter = codecs.decode(splitter, 'unicode_escape')
        return splitter

    def get_batch_data(self, batch_data, content_type):
        if content_type == 'paragraph':
            return batch_data, "original"
        elif content_type == 'sentence':
            try:
                return TextBatchData.objects.get(result=batch_data), "result"
            except TextBatchData.DoesNotExist:
                return batch_data, "original"

    def split_text(self, text):
        if '\n' in self.splitter:
            text = text.replace('\r\n', '\n')
        return [segment.strip() for segment in re.split(re.escape(self.splitter), text) if segment.strip()]

    # def _build_sentence(self, segmented_text, paragraph_index):
    #     for idx, segment in enumerate(segmented_text, start=1):
    #         yield {
    #             "sentence": segment,
    #             "paragraph_index": paragraph_index,
    #             "sentence_index": idx
    #         }

    def create_result_batch_data(self, batch_data, data, content_type):
        base_name = os.path.basename(batch_data.file.name)
        file_name, _ = os.path.splitext(base_name)
        output_dir = os.path.join(settings.MEDIA_ROOT, 'batch_files')
        os.makedirs(output_dir, exist_ok=True)

        # New relative path for the file
        new_file_name = f"{file_name}_segmented_{content_type}s.json"
        relative_path = f"batch_files/{new_file_name}"
        output_path = os.path.join(settings.MEDIA_ROOT, relative_path)

        self.file_writer._write_streaming_object(data, output_path)

        result_batch_data = TextBatchData.objects.create(
            batch=batch_data.plan,
            file_name=new_file_name,
            content_type=content_type,
        )
        result_batch_data.file.name = relative_path
        # Save the result related to the original batch_data
        result_batch_data.result = batch_data
        result_batch_data.save()

    def buffer_and_split(self, content, splitter):
        buffer = ""
        splitter_len = len(splitter)

        for line in content:
            buffer += line if line.endswith('\n') else line + '\n'
            while True:
                index = buffer.find(splitter)
                if index == -1:
                    break
                # Yield part before splitter
                part = buffer[:index]
                yield part.strip()
                # Remove yielded part + splitter from buffer
                buffer = buffer[index + splitter_len:]

        # Yield any remaining buffer after loop
        if buffer.strip():
            yield buffer.strip()

    def _build_segment(self, content):
        text = self.buffer_and_split(content, self.splitter)
        for index, segment in enumerate(text, start=1):
            print(segment)
            yield {"segment": segment, "index": index}

    def _segment_original_data(self, batch_data, content, content_type):
        data = self._build_segment(content)
        data_object = {
            f'{content_type}s': data
        }
        self.create_result_batch_data(batch_data, data_object, content_type)

        task_result = TextSegmentationTaskResult.objects.create(
            batch=self.batch,
            batch_data=batch_data,
            plan_segmentation=self.segmentation_plan,
            status='submitted',
            segmentation_result="\n".join(content),
        )

        return task_result

    def senetence_generator(self, paragraphs):
        for paragraph in paragraphs:
            sentences = self.split_text(paragraph['segment'])
            for index, sentence in enumerate(sentences, start=1):
                yield {
                    "sentence": sentence.strip(),
                    "paragraph_index": paragraph['index'],
                    "sentence_index": index
                }

    def _segement_result_data(self, paragraphs, batch_data, content_type):
        data = self.senetence_generator(paragraphs)
        sentences_result = {
            'sentences': data
        }
        self.create_result_batch_data(batch_data, sentences_result, content_type)
        all_sentences = list(self.senetence_generator(paragraphs))
        print(all_sentences)
        task_result = TextSegmentationTaskResult.objects.create(
            batch=self.batch,
            batch_data=batch_data,
            plan_segmentation=self.segmentation_plan,
            status='submitted',
            segmentation_result="\n".join(sentence['sentence'] for sentence in all_sentences),
        )
        return task_result

    def create_tasks_segmented_data(self, original_batch_data):
        batch_data, source_type = self.get_batch_data(original_batch_data, self.segmentation_plan.content_type)
        content = self.file_reader.stream_file(batch_data.file.path)

        if not content:
            raise ValueError("content is empty or missing.")
        if source_type == "original":
            task_result = self._segment_original_data(batch_data, content, self.segmentation_plan.content_type)
        elif source_type == "result":
            task_result = self._segement_result_data(content, original_batch_data,
                                                     self.segmentation_plan.content_type)
        else:
            raise ValueError("Unsupported source text type.")

        return task_result

    def process_batch_segmented_data_list(self):
        created_tasks = []

        for batch_data in self.batch_data_list:
            try:
                task = self.create_tasks_segmented_data(batch_data)
                created_tasks.append(task)

            except Exception as e:
                raise ValidationError(f"Failed to process BatchData ID {batch_data.id}: {str(e)}")
        return created_tasks
