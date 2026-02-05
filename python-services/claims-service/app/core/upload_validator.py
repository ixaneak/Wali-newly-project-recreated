"""
File Upload Validator for Claims Service
- Magic byte verification (JPEG, PNG only)
- File size limit (5MB max)
"""
from fastapi import HTTPException, UploadFile
from typing import Set
import io

# Magic bytes for allowed file types
MAGIC_BYTES = {
    b'\xff\xd8\xff': 'image/jpeg',  # JPEG
    b'\x89PNG\r\n\x1a\n': 'image/png',  # PNG
}

ALLOWED_MIME_TYPES: Set[str] = {'image/jpeg', 'image/png'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


class InvalidFileType(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=400,
            detail="Invalid file type. Only JPEG and PNG images are allowed."
        )


class FileTooLarge(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=413,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB."
        )


def detect_mime_type(file_bytes: bytes) -> str | None:
    """Detect MIME type from magic bytes."""
    for magic, mime_type in MAGIC_BYTES.items():
        if file_bytes.startswith(magic):
            return mime_type
    return None


async def validate_upload(file: UploadFile) -> bytes:
    """
    Validate uploaded file:
    1. Check file size (5MB max)
    2. Verify magic bytes match allowed types
    
    Returns the file bytes if valid.
    
    Usage:
        @app.post("/upload")
        async def upload_photo(file: UploadFile):
            file_bytes = await validate_upload(file)
            # Process valid file...
    """
    # Read file content
    content = await file.read()
    await file.seek(0)  # Reset for potential re-read
    
    # Check size
    if len(content) > MAX_FILE_SIZE:
        raise FileTooLarge()
    
    # Check magic bytes
    detected_type = detect_mime_type(content)
    if detected_type is None or detected_type not in ALLOWED_MIME_TYPES:
        raise InvalidFileType()
    
    return content


def validate_file_bytes(file_bytes: bytes) -> str:
    """
    Validate file bytes directly (for base64-decoded content).
    Returns the detected MIME type if valid.
    """
    if len(file_bytes) > MAX_FILE_SIZE:
        raise FileTooLarge()
    
    detected_type = detect_mime_type(file_bytes)
    if detected_type is None or detected_type not in ALLOWED_MIME_TYPES:
        raise InvalidFileType()
    
    return detected_type
