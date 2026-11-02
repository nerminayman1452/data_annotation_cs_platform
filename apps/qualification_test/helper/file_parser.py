
import pandas as pd
import json

class FileParser:
    def __init__(self, uploaded_file):
        self.uploaded_file = uploaded_file
        self.file_name = uploaded_file.name.lower()

    def parse(self):
        if self.file_name.endswith('.csv'):
            return pd.read_csv(self.uploaded_file)

        elif self.file_name.endswith(('.xls', '.xlsx')):
            return pd.read_excel(self.uploaded_file)

        elif self.file_name.endswith('.json'):
            content = self.uploaded_file.read().decode('utf-8')
            data = json.loads(content)
            return pd.DataFrame(data)

        raise ValueError("Unsupported file format. Use .csv, .xlsx, .xls, or .json.")
