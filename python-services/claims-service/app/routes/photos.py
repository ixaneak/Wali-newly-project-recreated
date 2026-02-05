"""Photos API routes for claims-service."""
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from typing import List
import logging

from app.core.storage import minio_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/photos", tags=["photos"])

@router.post("/upload", response_model=dict)
async def upload_photo(file: UploadFile = File(...)):
    """
    Upload a single claim photo to MinIO.
    """
    try:
        contents = await file.read()
        filename = file.filename or "image.jpg"
        extension = "." + filename.split(".")[-1].lower() if "." in filename else ".jpg"
        
        # We don't have a claim_id yet if this is called before claim creation
        # or we use a temporary session id. For now, we use a generic path.
        object_name = minio_client.upload_image(contents, "pending", extension)
        url = minio_client.get_presigned_url(object_name)
        
        return {
            "url": url,
            "object_name": object_name,
            "status": "uploaded"
        }
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )

@router.post("/upload-multiple", response_model=dict)
async def upload_multiple_photos(files: List[UploadFile] = File(...)):
    """Upload multiple claim photos at once."""
    urls = []
    
    for file in files:
        try:
            result = await upload_photo(file)
            urls.append(result["url"])
        except Exception as e:
            logger.error(f"Failed to upload {file.filename}: {e}")
    
    return {
        "urls": urls,
        "count": len(urls)
    }
