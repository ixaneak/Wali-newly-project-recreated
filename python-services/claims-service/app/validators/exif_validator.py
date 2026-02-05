"""EXIF metadata validation for claim images."""
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import piexif
from datetime import datetime, timedelta
from io import BytesIO
import logging

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Ivory Coast bounding box (approximate)
IVORY_COAST_BOUNDS = {
    "min_lat": 4.0,
    "max_lat": 10.8,
    "min_lon": -8.6,
    "max_lon": -2.5
}


class EXIFValidator:
    """Validate EXIF metadata in claim images."""
    
    @staticmethod
    def validate_image(image_data: bytes) -> dict:
        """
        Validate EXIF metadata for a claim image.
        
        Args:
            image_data: Binary image data
        
        Returns:
            Dict with validation results and extracted EXIF data
        
        Raises:
            ValueError: If validation fails
        """
        result = {
            "valid": False,
            "errors": [],
            "exif_data": {}
        }
        
        try:
            image = Image.open(BytesIO(image_data))
        except Exception as e:
            result["errors"].append(f"Invalid image file: {str(e)}")
            return result
        
        # Check image dimensions
        width, height = image.size
        min_width, min_height = settings.min_image_dimensions
        
        if width < min_width or height < min_height:
            result["errors"].append(
                f"Image too small: {width}x{height} (minimum {min_width}x{min_height})"
            )
        
        # Extract EXIF data
        try:
            exif_dict = piexif.load(image.info.get("exif", b""))
        except Exception as e:
            result["errors"].append("No EXIF data found - possible screenshot")
            logger.warning(f"EXIF extraction failed: {e}")
            return result
        
        # Validate GPS coordinates
        gps_data = exif_dict.get("GPS", {})
        if gps_data:
            gps_valid, gps_coords = EXIFValidator._validate_gps(gps_data)
            if gps_valid:
                result["exif_data"]["gps"] = gps_coords
            else:
                result["errors"].append("GPS coordinates outside Ivory Coast")
        else:
            result["errors"].append("No GPS data found in image")
        
        # Validate timestamp
        exif_0th = exif_dict.get("0th", {})
        exif_exif = exif_dict.get("Exif", {})
        
        timestamp_valid, timestamp = EXIFValidator._validate_timestamp(exif_0th, exif_exif)
        if timestamp_valid:
            result["exif_data"]["timestamp"] = timestamp
        else:
            result["errors"].append(f"Image timestamp older than {settings.exif_timestamp_hours_limit} hours")
        
        # Extract camera model
        camera_model = exif_0th.get(piexif.ImageIFD.Model)
        if camera_model:
            result["exif_data"]["camera_model"] = camera_model.decode() if isinstance(camera_model, bytes) else camera_model
        else:
            result["errors"].append("No camera model found - possible screenshot")
        
        # Validation result
        result["valid"] = len(result["errors"]) == 0
        
        return result
    
    @staticmethod
    def _validate_gps(gps_data: dict) -> tuple[bool, dict]:
        """Validate GPS coordinates are within Ivory Coast."""
        try:
            # Extract latitude
            lat_ref = gps_data.get(piexif.GPSIFD.GPSLatitudeRef, b"N").decode()
            lat_tuple = gps_data.get(piexif.GPSIFD.GPSLatitude)
            
            if lat_tuple:
                lat = EXIFValidator._convert_to_degrees(lat_tuple)
                if lat_ref == "S":
                    lat = -lat
            else:
                return False, {}
            
            # Extract longitude
            lon_ref = gps_data.get(piexif.GPSIFD.GPSLongitudeRef, b"E").decode()
            lon_tuple = gps_data.get(piexif.GPSIFD.GPSLongitude)
            
            if lon_tuple:
                lon = EXIFValidator._convert_to_degrees(lon_tuple)
                if lon_ref == "W":
                    lon = -lon
            else:
                return False, {}
            
            # Check if coordinates are within Ivory Coast
            in_bounds = (
                IVORY_COAST_BOUNDS["min_lat"] <= lat <= IVORY_COAST_BOUNDS["max_lat"] and
                IVORY_COAST_BOUNDS["min_lon"] <= lon <= IVORY_COAST_BOUNDS["max_lon"]
            )
            
            coords = {
                "latitude": lat,
                "longitude": lon,
                "in_ivory_coast": in_bounds
            }
            
            return in_bounds, coords
            
        except Exception as e:
            logger.error(f"GPS validation error: {e}")
            return False, {}
    
    @staticmethod
    def _convert_to_degrees(value: tuple) -> float:
        """Convert GPS coordinates to degrees."""
        d, m, s = value
        return float(d[0]) / float(d[1]) + \
               (float(m[0]) / float(m[1])) / 60.0 + \
               (float(s[0]) / float(s[1])) / 3600.0
    
    @staticmethod
    def _validate_timestamp(exif_0th: dict, exif_exif: dict) -> tuple[bool, str]:
        """Validate image timestamp is within acceptable range."""
        # Try multiple timestamp fields
        timestamp_str = None
        
        # DateTime original (preferred)
        if piexif.ExifIFD.DateTimeOriginal in exif_exif:
            timestamp_str = exif_exif[piexif.ExifIFD.DateTimeOriginal]
        # DateTime
        elif piexif.ImageIFD.DateTime in exif_0th:
            timestamp_str = exif_0th[piexif.ImageIFD.DateTime]
        
        if not timestamp_str:
            return False, ""
        
        # Decode if bytes
        if isinstance(timestamp_str, bytes):
            timestamp_str = timestamp_str.decode()
        
        try:
            # Parse timestamp (format: "2026:01:27 12:30:45")
            timestamp = datetime.strptime(timestamp_str, "%Y:%m:%d %H:%M:%S")
            
            # Check if within allowed time window
            time_diff = datetime.now() - timestamp
            max_age = timedelta(hours=settings.exif_timestamp_hours_limit)
            
            if time_diff > max_age:
                return False, timestamp.isoformat()
            
            # Reject future timestamps (clock manipulation)
            if time_diff < timedelta(hours=-1):
                return False, timestamp.isoformat()
            
            return True, timestamp.isoformat()
            
        except Exception as e:
            logger.error(f"Timestamp parsing error: {e}")
            return False, ""
