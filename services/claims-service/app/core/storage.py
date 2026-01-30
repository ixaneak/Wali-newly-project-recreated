"""MinIO storage client for claims images."""
from minio import Minio
from minio.error import S3Error
from io import BytesIO
import uuid
from datetime import timedelta
import logging

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class MinIOClient:
    """MinIO client for uploading and managing claim images."""
    
    def __init__(self):
        self.healthy = False
        try:
            self.client = Minio(
                settings.minio_endpoint,
                access_key=settings.minio_access_key,
                secret_key=settings.minio_secret_key,
                secure=settings.minio_secure
            )
            self.bucket_name = settings.minio_bucket_name
            self._ensure_bucket_exists()
            self.healthy = True
        except Exception as e:
            logger.error(f"MinIO initialization failed: {e}")
            if settings.environment == "production":
                raise
            logger.warning("Continuing without MinIO storage (MOCK MODE)")
    
    def _ensure_bucket_exists(self):
        """Create bucket if it doesn't exist."""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"Created MinIO bucket: {self.bucket_name}")
        except S3Error as e:
            logger.error(f"Error ensuring bucket exists: {e}")
            raise
    
    def upload_image(
        self, 
        image_data: bytes, 
        claim_id: str, 
        file_extension: str = ".jpg"
    ) -> str:
        """
        Upload claim image to MinIO.
        
        Args:
            image_data: Binary image data
            claim_id: Claim UUID
            file_extension: File extension (.jpg, .png, etc.)
        
        Returns:
            Object name (path) in MinIO
        """
        object_name = f"claims/{claim_id}/{uuid.uuid4()}{file_extension}"
        
        if not self.healthy:
            logger.warning(f"Mock upload: {object_name}")
            return object_name
            
        try:
            self.client.put_object(
                self.bucket_name,
                object_name,
                BytesIO(image_data),
                length=len(image_data),
                content_type=f"image/{file_extension.strip('.')}"
            )
            logger.info(f"Uploaded image to MinIO: {object_name}")
            return object_name
        except Exception as e:
            logger.error(f"Error uploading image: {e}")
            raise
    
    def get_presigned_url(self, object_name: str, expires_hours: int = 24) -> str:
        """
        Get presigned URL for downloading an image.
        
        Args:
            object_name: MinIO object path
            expires_hours: URL expiration time
        
        Returns:
            Presigned URL string
        """
        if not self.healthy:
            return f"https://via.placeholder.com/800?text={object_name}"
            
        try:
            url = self.client.presigned_get_object(
                self.bucket_name,
                object_name,
                expires=timedelta(hours=expires_hours)
            )
            return url
        except Exception as e:
            logger.error(f"Error generating presigned URL: {e}")
            raise
    
    def delete_image(self, object_name: str):
        """Delete an image from MinIO."""
        try:
            self.client.remove_object(self.bucket_name, object_name)
            logger.info(f"Deleted image from MinIO: {object_name}")
        except S3Error as e:
            logger.error(f"Error deleting image: {e}")
            raise
    
        if not self.healthy:
            return []
            
        prefix = f"claims/{claim_id}/"
        try:
            objects = self.client.list_objects(self.bucket_name, prefix=prefix)
            return [obj.object_name for obj in objects]
        except Exception as e:
            logger.error(f"Error listing images: {e}")
            return []


# Global MinIO client instance
minio_client = MinIOClient()
