import csv
import json
import os
from openpyxl import load_workbook


class FileLoader:
    """
    Responsible ONLY for reading raw file content.
    One public entry point: load()
    """

    def load(self, file_path: str) :
        ext = self._get_extension(file_path)

        handlers = {
            "txt": self._load_text,
            "json": self._load_json,
            "csv": self._load_csv,
            "xlsx": self._load_xlsx,
        }

        if ext not in handlers:
            raise ValueError(f"Unsupported file type: {ext}")

        return handlers[ext](file_path)

    # ---------------- PRIVATE HANDLERS ---------------- #

    def _load_text(self, file_path: str):
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def _load_json(self, file_path: str) :
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _load_csv(self, file_path: str) :
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            return list(csv.DictReader(f))

    def _load_xlsx(self, file_path: str):
        wb = load_workbook(file_path, data_only=True)
        sheet = wb.active

        rows = list(sheet.iter_rows(values_only=True))
        if not rows:
            return []

        headers = [str(h).strip() for h in rows[0]]

        data = []
        for row in rows[1:]:
            item = {headers[i]: row[i] for i in range(len(headers))}
            data.append(item)

        return data

    # ---------------- UTILITIES ---------------- #

    def _get_extension(self, file_path: str) -> str:
        return os.path.splitext(file_path)[1].lower().lstrip(".")