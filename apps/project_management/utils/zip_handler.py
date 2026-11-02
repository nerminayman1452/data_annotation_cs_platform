import os
import mimetypes
from io import BytesIO
from zipfile import ZipFile

from django.core.files.uploadedfile import InMemoryUploadedFile


def extract_zip_file(file_obj):
    """Extract files from an uploaded zip file and return a dict of
    {filename: InMemoryUploadedFile} suitable for passing into DRF/Django
    serializers and model FileFields.

    - Skips directories and files without an extension.
    - Preserves the base filename only (no directories).
    """
    result = {}
    # ZipFile can accept a file-like object
    with ZipFile(file_obj, 'r') as zf:
        for member in zf.namelist():
            # skip directories
            if member.endswith('/'):
                continue
            # skip files without an extension
            if '.' not in member:
                continue

            data = zf.read(member)
            if not data:
                continue

            bio = BytesIO(data)
            name = os.path.basename(member)
            content_type = mimetypes.guess_type(name)[0] or 'application/octet-stream'
            uploaded = InMemoryUploadedFile(
                bio, 'file', name, content_type, len(data), None
            )
            result[name] = uploaded

    return result
