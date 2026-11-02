import json
import os

import ijson
from docx import Document


class FileReader:

    @staticmethod
    def read(file_path):
        """
        Extracts text content from the uploaded file in the given BatchData instance.
        Supports .txt and .docx files.
        Returns the content as a string.
        """
        if not file_path:
            return ""
        ext = os.path.splitext(file_path)[1].lower()
        try:
            if ext == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            elif ext == '.docx':
                doc = Document(file_path)
                return "\n".join([para.text for para in doc.paragraphs])
            elif ext == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return ""
        except Exception:
            return ""

    def stream_txt_files(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                yield line.strip()

    def stream_docx_files(self, file_path):
        with open(file_path, 'rb') as file:
            document = Document(file)
            for paragraph in document.paragraphs:
                text = paragraph.text.strip()
                if text:
                    yield text

    def stream_first_array_items(self, json_file_path):

        with open(json_file_path, 'r', encoding='utf-8') as f:
            # Initialize ijson parser
            parser = ijson.parse(f)
            current_key = None

            for prefix, event, value in parser:
                if event == 'start_array' and prefix:
                    current_key = prefix
                    break  # Found the first array

        if not current_key:
            raise ValueError("No top-level array found in the JSON file.")
        return current_key

    def stream_json_file(self, file_path):
        try:
            key = self.stream_first_array_items(file_path)

            with open(file_path, 'rb') as f:
                for item in ijson.items(f, f'{key}.item'):
                    yield item
        except Exception as e:
            print(f"Error streaming {key}: {e}")
            return

    def stream_file(self, file_path):

        if not file_path:
            return ""
        ext = os.path.splitext(file_path)[1].lower()
        stream_file_type = {
            '.txt': self.stream_txt_files,
            '.docx': self.stream_docx_files,
            '.json': self.stream_json_file
        }.get(ext)
        if stream_file_type:
            return stream_file_type(file_path)
        return None
