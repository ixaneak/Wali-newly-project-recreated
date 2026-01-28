"""
Photo storage with Cloudinary.
Simple upload endpoint for claim photos.
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
import cloudinary
import cloudinary.uploader
import base64
import uuid
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/api/v1/photos", tags=["photos"])

# Configure Cloudinary (if credentials exist)
CLOUDINARY_ENABLED = False
try:
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME")
    api_key = os.getenv("CLOUDINARY_API_KEY")
    api_secret = os.getenv("CLOUDINARY_API_SECRET")
    
    if cloud_name and api_key and api_secret:
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret
        )
        CLOUDINARY_ENABLED = True
except Exception:
    pass


@router.post("/upload", response_model=dict)
async def upload_photo(file: UploadFile = File(...)):
    """
    Upload a claim photo.
    
    - If Cloudinary is configured, uploads to cloud and returns URL
    - Otherwise, returns base64 data URL for storage in database
    """
    try:
        # Read file content
        contents = await file.read()
        
        if CLOUDINARY_ENABLED:
            # Upload to Cloudinary
            result = cloudinary.uploader.upload(
                contents,
                folder="wali/claims",
                public_id=f"claim_{uuid.uuid4()}",
                resource_type="image"
            )
            return {
                "url": result["secure_url"],
                "public_id": result["public_id"],
                "storage": "cloudinary"
            }
        else:
            # Fallback: Return base64 data URL
            base64_data = base64.b64encode(contents).decode('utf-8')
            mime_type = file.content_type or "image/jpeg"
            data_url = f"data:{mime_type};base64,{base64_data}"
            
            return {
                "url": data_url,
                "storage": "base64",
                "warning": "Cloudinary not configured, using base64 fallback"
            }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/upload-multiple", response_model=dict)
async def upload_multiple_photos(files: List[UploadFile] = File(...)):
    """Upload multiple claim photos at once."""
    results = []
    
    for file in files:
        try:
            result = await upload_photo(file)
            results.append(result)
        except Exception as e:
            results.append({"error": str(e), "filename": file.filename})
    
    return {
        "uploaded": len([r for r in results if "url" in r]),
        "failed": len([r for r in results if "error" in r]),
        "results": results
    }
