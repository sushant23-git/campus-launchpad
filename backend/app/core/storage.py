import os
import uuid
import shutil
from typing import BinaryIO, Tuple
from fastapi import UploadFile
from app.core.config import settings
from app.core.exceptions import BusinessRuleException

ALLOWED_EXTENSIONS = {
    # Documents
    "pdf", "docx", "doc", "txt", "md",
    # Images
    "png", "jpg", "jpeg", "gif",
    # Code/Archives
    "zip", "tar.gz", "py", "js", "json"
}

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
    "text/plain",
    "text/markdown",
    "image/png",
    "image/jpeg",
    "image/gif",
    "application/zip",
    "application/x-tar",
    "text/x-python",
    "text/javascript",
    "application/json"
}

MAX_FILE_SIZE = 10 * 1024 * 1024 # 10 Megabytes

class StorageProvider:
    """Abstract/base storage manager defining standard write interfaces."""
    def save_file(self, file: UploadFile) -> Tuple[str, str]:
        """Save file to storage, returns a tuple of (saved_file_name, storage_path)."""
        raise NotImplementedError()

    def get_file_path(self, storage_path: str) -> str:
        """Get absolute path or download link for the resource."""
        raise NotImplementedError()


class LocalStorageProvider(StorageProvider):
    def __init__(self):
        self.upload_dir = settings.FILE_STORAGE_PATH
        os.makedirs(self.upload_dir, exist_ok=True)

    def save_file(self, file: UploadFile) -> tuple[str, str]:
        """Validate and write uploaded file to the local disk upload directory."""
        # 1. Validate File Size
        file.file.seek(0, os.SEEK_END)
        file_size = file.file.tell()
        file.file.seek(0) # Reset pointer
        
        if file_size > MAX_FILE_SIZE:
            raise BusinessRuleException(f"File size exceeds the maximum limit of 10MB (file size: {file_size / (1024*1024):.2f}MB).")

        # 2. Validate Extension
        filename = file.filename or "unknown"
        ext = filename.split(".")[-1].lower() if "." in filename else ""
        if ext not in ALLOWED_EXTENSIONS:
            raise BusinessRuleException(f"File extension '.{ext}' is not permitted.")

        # 3. Validate MIME type
        content_type = file.content_type
        if content_type not in ALLOWED_MIME_TYPES:
            raise BusinessRuleException(f"MIME type '{content_type}' is not permitted.")

        # 4. Generate secure UUID filename to prevent arbitrary execution & path traversal
        secure_name = f"{uuid.uuid4()}.{ext}"
        storage_path = os.path.join(self.upload_dir, secure_name)

        # Write to disk
        with open(storage_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return secure_name, storage_path

    def get_file_path(self, storage_path: str) -> str:
        """Return absolute path of the resource on local disk."""
        return os.path.abspath(storage_path)


# Factory to get storage client
def get_storage_provider() -> StorageProvider:
    if settings.FILE_STORAGE_PROVIDER == "local":
        return LocalStorageProvider()
    else:
        # Falls back to local disk during development
        return LocalStorageProvider()
