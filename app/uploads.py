# TracePass code note: This module implements the app/uploads.py part of the application.
import mimetypes
import os

from flask import abort
from werkzeug.utils import secure_filename

try:
    from PIL import Image
except ImportError:
    Image = None

ALLOWED_MIME_BY_EXT = {
    "pdf": {"application/pdf"},
    "png": {"image/png"},
    "jpg": {"image/jpeg"},
    "jpeg": {"image/jpeg"},
    "webp": {"image/webp"},
    "docx": {"application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/zip"},
    "xlsx": {"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "application/zip"},
}

# Code explanation: Implement the `validate upload` operation used by this part of TracePass.
def validate_upload(file_storage, allowed_extensions):
    """Validate extension, MIME and basic file signature before saving."""
    if not file_storage or not file_storage.filename:
        abort(400, description="A file is required.")
    name = secure_filename(file_storage.filename)
    ext = os.path.splitext(name)[1].lower().lstrip(".")
    if ext not in allowed_extensions:
        abort(400, description=f"Unsupported upload type: .{ext or 'unknown'}")
    mime = (file_storage.mimetype or mimetypes.guess_type(name)[0] or "").lower()
    allowed_mimes = ALLOWED_MIME_BY_EXT.get(ext, set())
    stream = file_storage.stream
    pos = stream.tell()
    header = stream.read(16)
    stream.seek(pos)
    if mime not in allowed_mimes and mime not in {"application/octet-stream", "binary/octet-stream", ""}:
        abort(400, description="The uploaded file MIME type is not permitted.")
    if ext == "pdf" and not header.startswith(b"%PDF"):
        abort(400, description="The uploaded file is not a valid PDF.")
    if ext in {"png", "jpg", "jpeg", "webp"}:
        if Image is None:
            abort(500, description="Image validation dependency is unavailable.")
        try:
            stream.seek(0)
            with Image.open(stream) as image:
                image.verify()
        except Exception:
            abort(400, description="The uploaded file is not a valid image.")
        finally:
            stream.seek(0)
    if ext in {"docx", "xlsx"} and not header.startswith(b"PK"):
        abort(400, description="The uploaded Office document is invalid.")
    return True
