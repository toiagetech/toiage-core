import uuid
from datetime import datetime
from pathlib import Path

from fastapi import UploadFile

from app.core.config import settings

ALLOWED_MIME_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}


def _validate_image(file: UploadFile) -> None:
    """Validate file type and size."""
    if file.content_type not in ALLOWED_MIME_TYPES:
        allowed = ", ".join(ALLOWED_MIME_TYPES)
        raise ValueError(
            f"Invalid file type '{file.content_type}'. Allowed: {allowed}"
        )

    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    file.file.seek(0, 2)  # seek to end
    size = file.file.tell()
    file.file.seek(0)  # reset

    if size > max_bytes:
        raise ValueError(
            f"File too large ({size / 1024 / 1024:.1f} MB). "
            f"Max: {settings.MAX_UPLOAD_SIZE_MB} MB"
        )


def save_upload(file: UploadFile) -> dict:
    """Save an uploaded image to local storage and return metadata."""
    _validate_image(file)

    ext = ALLOWED_MIME_TYPES[file.content_type]
    unique_name = f"{uuid.uuid4().hex}{ext}"

    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_path = upload_dir / unique_name
    content = file.file.read()
    file_path.write_bytes(content)

    file_size = len(content)

    return {
        "filename": unique_name,
        "original_name": file.filename or unique_name,
        "file_size": file_size,
        "mime_type": file.content_type,
        "url": f"/uploads/files/{unique_name}",
    }
