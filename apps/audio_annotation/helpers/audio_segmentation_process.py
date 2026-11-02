import os

from django.conf import settings
from django.core.exceptions import ValidationError
from pydub import AudioSegment
from pydub.silence import split_on_silence

from apps.audio_annotation.models.plan_audio_segmentation import AudioSegmentationPlan
from apps.audio_annotation.models.task_audio_segmentation import AudioSegmentationTaskResult
from apps.project_management.models.audio_plan import AudioPlanRawData
from apps.project_management.models.batch import Batch



class AudioSegmentationProcessor:
    def __init__(self, plan_id, batch_id, request):
        self.segmentation_plan = AudioSegmentationPlan.objects.filter(id=plan_id).first()
        self.segment_duration = self.segmentation_plan.maximum_segment_duration * 1000  # ms
        self.batch_data_list = AudioPlanRawData.objects.filter(batch=batch_id, result__isnull=True)
        self.batch = Batch.objects.get(id=batch_id)

    def load_audio_file(self, file):
        return AudioSegment.from_file(file)

    def split_audio_file(self, audio):
        chunks = split_on_silence(
            audio,
            min_silence_len=1000,
            silence_thresh=audio.dBFS - 16,
            keep_silence=500
        )
        segments = []
        current = AudioSegment.empty()
        start_time = 0
        for chunk in chunks:
            if len(current) + len(chunk) <= self.segment_duration:
                current += chunk
            else:
                yield current, start_time
                start_time += len(current) / 1000
                current = chunk
        if len(current) > 0:
            yield current, start_time

    # def save_segment(self,segment,output_path):
    #     segment_file = BytesIO()
    #     segment_file.seek(0)

    def create_result_batch_data(self, batch_data, segment, index):
        base_name = os.path.basename(batch_data.file.name)
        file_name, _ = os.path.splitext(base_name)
        output_dir = os.path.join(settings.MEDIA_ROOT, 'batch_files')
        os.makedirs(output_dir, exist_ok=True)
        # New relative path for the file
        new_file_name = f"{file_name}_segmented_{index}.mp3"
        relative_path = f"batch_files/{new_file_name}"
        output_path = os.path.join(settings.MEDIA_ROOT, relative_path)
        segment.export(output_path, format="mp3")

        result_batch_data = AudioPlanRawData.objects.create(
            batch=batch_data.plan,
            file_name=new_file_name,
        )
        result_batch_data.file.name = relative_path
        # Save the result related to the original batch_data
        result_batch_data.result = batch_data
        result_batch_data.save()

    def create_segment_task(self, batch_data, segment, index, start_time):

        return AudioSegmentationTaskResult.objects.create(
            batch=self.batch,
            batch_data=batch_data,
            plan_segmentation=self.segmentation_plan,
            status='submitted',
            phase_index=index,
            segment_start_time=start_time,
            segment_end_time=start_time + len(segment) / 1000
        )

    def process_audio_file_segments(self, batch_data, segment_generator):

        for index, (segment, start_time) in enumerate(segment_generator, start=1):
            self.create_result_batch_data(batch_data, segment, index)
            yield self.create_segment_task(batch_data, segment, index, start_time)

    def process_batch_segmented_data_list(self):
        created_tasks = []
        for batch_data in self.batch_data_list:
            try:
                audio = self.load_audio_file(batch_data.file.path)
                segment_generator = self.split_audio_file(audio)
                for task in self.process_audio_file_segments(batch_data, segment_generator):
                    created_tasks.append(task)
            except Exception as e:
                raise ValidationError(f"Failed to process BatchData ID {batch_data.id}: {str(e)}")
        return created_tasks
