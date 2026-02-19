"""
Image Forensics Service for Fraud Detection.

Detects:
- Duplicate claims (perceptual hashing)
- Location fraud (GPS validation)
- Stale photos (EXIF timestamp analysis)
- Stock images (screenshot detection)
- Velocity fraud (claim frequency)
"""
import hashlib
import io
import logging
import math
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

import aiohttp
from PIL import ExifTags, Image, UnidentifiedImageError
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.claims import Claim, FraudCheckResult, FraudCheckType, FraudLog

logger = logging.getLogger(__name__)

# Constants
MAX_IMAGE_SIZE_MB = 10
SUPPORTED_FORMATS = {"JPEG", "PNG", "JPG"}
HAMMING_DISTANCE_THRESHOLD = 10  # For duplicate detection
GPS_DISTANCE_THRESHOLD_KM = 1.0  # Flag if > 1km from pharmacy
GPS_DISTANCE_AUTO_REJECT_KM = 50.0  # Auto-reject if > 50km
STALE_IMAGE_HOURS = 24  # Flag if photo taken > 24h ago
VELOCITY_CLAIM_LIMIT = 3  # Max claims per hour

# Screenshot aspect ratios (common phone screenshot ratios)
SCREENSHOT_RATIOS = {
    (16, 9),    # Standard
    (19, 9),    # Modern phones
    (19.5, 9),  # iPhone
    (20, 9),    # Samsung
    (18, 9),    # Older phones
}


@dataclass
class FraudReport:
    """Result of image forensics analysis."""
    is_suspicious: bool
    risk_score: float
    flags: List[str]
    perceptual_hash: str
    gps_coordinates: Optional[Tuple[float, float]]
    exif_timestamp: Optional[datetime]
    device_info: Optional[Dict[str, str]]
    
    def __post_init__(self):
        """Ensure risk score is capped at 1.0."""
        self.risk_score = min(1.0, self.risk_score)


class ImageForensicsService:
    """
    Service for analyzing claim images for fraud.
    
    Performs multiple checks:
    1. Perceptual hashing for duplicate detection
    2. EXIF GPS validation
    3. EXIF timestamp analysis
    4. Screenshot detection
    5. Velocity checking
    """
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def analyze(
        self,
        image_bytes: bytes,
        context: Dict[str, any]
    ) -> FraudReport:
        """
        Perform complete fraud analysis on an image.
        
        Args:
            image_bytes: Raw image data
            context: {
                'claim_id': str,
                'artisan_phone': str,
                'claim_type': str,
                'pharmacy_id': str (optional),
                'submitted_at': datetime,
                'device_fingerprint': str (optional)
            }
        
        Returns:
            FraudReport with risk score and flags
        """
        flags = []
        risk_score = 0.0
        
        # Validate image size
        if len(image_bytes) > MAX_IMAGE_SIZE_MB * 1024 * 1024:
            return FraudReport(
                is_suspicious=True,
                risk_score=1.0,
                flags=["IMAGE_TOO_LARGE"],
                perceptual_hash="",
                gps_coordinates=None,
                exif_timestamp=None,
                device_info=None
            )
        
        try:
            # Load image
            image = Image.open(io.BytesIO(image_bytes))
            
            # Validate format
            if image.format not in SUPPORTED_FORMATS:
                return FraudReport(
                    is_suspicious=True,
                    risk_score=0.5,
                    flags=["UNSUPPORTED_FORMAT"],
                    perceptual_hash="",
                    gps_coordinates=None,
                    exif_timestamp=None,
                    device_info=None
                )
            
            # 1. Perceptual Hashing
            phash = self._compute_perceptual_hash(image)
            duplicate_score = await self._check_duplicate_image(phash, context.get("claim_id"))
            if duplicate_score > 0:
                flags.append("DUPLICATE_IMAGE")
                risk_score += duplicate_score
                await self._log_fraud_check(
                    context["claim_id"],
                    FraudCheckType.PERCEPTUAL_HASH,
                    FraudCheckResult.FAIL if duplicate_score > 0.3 else FraudCheckResult.SUSPICIOUS,
                    duplicate_score,
                    {"hash": phash, "matches_found": True}
                )
            
            # 2. EXIF Extraction
            exif_data = self._extract_exif(image)
            gps_coords = self._extract_gps(exif_data)
            exif_timestamp = self._extract_timestamp(exif_data)
            device_info = self._extract_device_info(exif_data)
            
            # 3. GPS Validation (for pharmacy claims)
            if context.get("claim_type") == "pharmacy" and gps_coords and context.get("pharmacy_id"):
                distance_score = await self._validate_gps_distance(
                    gps_coords, context["pharmacy_id"], context["claim_id"]
                )
                if distance_score > 0:
                    if distance_score >= 1.0:  # Auto-reject threshold
                        flags.append("IMPOSSIBLE_DISTANCE")
                    else:
                        flags.append("GPS_MISMATCH")
                    risk_score += min(0.3, distance_score)
            
            # 4. Temporal Analysis
            if exif_timestamp and context.get("submitted_at"):
                temporal_score = self._analyze_timestamp(
                    exif_timestamp, context["submitted_at"], context["claim_id"]
                )
                if temporal_score > 0:
                    flags.append("STALE_IMAGE" if temporal_score < 0.5 else "TAMPERED_TIMESTAMP")
                    risk_score += temporal_score
            
            # 5. Screenshot Detection
            screenshot_score = self._detect_screenshot(image, exif_data)
            if screenshot_score > 0:
                flags.append("SCREENSHOT_DETECTED")
                risk_score += screenshot_score
                await self._log_fraud_check(
                    context["claim_id"],
                    FraudCheckType.SCREENSHOT,
                    FraudCheckResult.FAIL,
                    screenshot_score,
                    {"aspect_ratio": image.size}
                )
            
            # 6. Velocity Check
            velocity_score = await self._check_velocity(
                context.get("artisan_phone"), context["claim_id"]
            )
            if velocity_score > 0:
                flags.append("VELOCITY_EXCEEDED")
                risk_score += velocity_score
            
            # 7. Device Mismatch (if enrollment fingerprint available)
            if context.get("device_fingerprint") and device_info:
                # Compare with enrollment device
                # This would query the artisan's enrollment record
                pass  # Implementation depends on artisan model
            
            return FraudReport(
                is_suspicious=risk_score >= 0.7,
                risk_score=risk_score,
                flags=flags,
                perceptual_hash=phash,
                gps_coordinates=gps_coords,
                exif_timestamp=exif_timestamp,
                device_info=device_info
            )
            
        except UnidentifiedImageError:
            logger.error(f"Cannot identify image for claim {context.get('claim_id')}")
            await self._log_fraud_check(
                context["claim_id"],
                FraudCheckType.SCREENSHOT,
                FraudCheckResult.FAIL,
                0.5,
                {"error": "UnidentifiedImageError"}
            )
            return FraudReport(
                is_suspicious=True,
                risk_score=0.5,
                flags=["CORRUPT_IMAGE"],
                perceptual_hash="",
                gps_coordinates=None,
                exif_timestamp=None,
                device_info=None
            )
        except Exception as e:
            logger.exception(f"Error analyzing image: {e}")
            # Circuit breaker: If fraud service fails, return suspicious with system flag
            return FraudReport(
                is_suspicious=True,
                risk_score=0.0,
                flags=["SYSTEM_UNABLE_TO_VERIFY"],
                perceptual_hash="",
                gps_coordinates=None,
                exif_timestamp=None,
                device_info=None
            )
    
    def _compute_perceptual_hash(self, image: Image.Image) -> str:
        """
        Compute dHash (difference hash) for perceptual similarity.
        
        Returns hex string of the hash.
        """
        # Convert to grayscale and resize to 9x8
        image = image.convert("L").resize((9, 8), Image.Resampling.LANCZOS)
        
        pixels = list(image.getdata())
        
        # Compute difference hash
        diff = []
        for row in range(8):
            for col in range(8):
                left_pixel = pixels[row * 9 + col]
                right_pixel = pixels[row * 9 + col + 1]
                diff.append(left_pixel > right_pixel)
        
        # Convert to hex
        decimal_value = sum(bit << i for i, bit in enumerate(diff))
        return format(decimal_value, '016x')
    
    def _hamming_distance(self, hash1: str, hash2: str) -> int:
        """Calculate Hamming distance between two hex hashes."""
        if len(hash1) != len(hash2):
            return float('inf')
        
        int1 = int(hash1, 16)
        int2 = int(hash2, 16)
        xor = int1 ^ int2
        return bin(xor).count('1')
    
    async def _check_duplicate_image(
        self,
        phash: str,
        claim_id: str
    ) -> float:
        """
        Check for duplicate or similar images.
        
        Returns risk score contribution (0.0 to 0.4).
        """
        try:
            # Query for existing claims with similar hashes
            result = await self.db.execute(
                select(Claim).where(
                    Claim.image_hash.isnot(None),
                    Claim.id != claim_id
                )
            )
            existing_claims = result.scalars().all()
            
            for claim in existing_claims:
                if claim.image_hash:
                    distance = self._hamming_distance(phash, claim.image_hash)
                    if distance == 0:
                        # Exact match
                        logger.warning(f"Exact duplicate image detected: claim {claim_id} matches {claim.id}")
                        return 0.4
                    elif distance < HAMMING_DISTANCE_THRESHOLD:
                        # Similar image
                        logger.warning(f"Similar image detected: claim {claim_id} ~ {claim.id} (distance={distance})")
                        return 0.4 * (1 - distance / HAMMING_DISTANCE_THRESHOLD)
            
            return 0.0
        except Exception as e:
            logger.error(f"Error checking duplicate image: {e}")
            return 0.0
    
    def _extract_exif(self, image: Image.Image) -> Dict:
        """Extract EXIF data from image."""
        try:
            return image._getexif() or {}
        except:
            return {}
    
    def _extract_gps(self, exif_data: Dict) -> Optional[Tuple[float, float]]:
        """Extract GPS coordinates from EXIF."""
        try:
            gps_info = exif_data.get(34853)  # GPSInfo tag
            if not gps_info:
                return None
            
            def convert_to_degrees(value):
                """Convert GPS coordinates to degrees."""
                d = float(value[0])
                m = float(value[1])
                s = float(value[2])
                return d + (m / 60.0) + (s / 3600.0)
            
            lat = convert_to_degrees(gps_info[2])  # GPSLatitude
            lat_ref = gps_info[1]  # GPSLatitudeRef
            if lat_ref != 'N':
                lat = -lat
            
            lon = convert_to_degrees(gps_info[4])  # GPSLongitude
            lon_ref = gps_info[3]  # GPSLongitudeRef
            if lon_ref != 'E':
                lon = -lon
            
            return (lat, lon)
        except:
            return None
    
    def _extract_timestamp(self, exif_data: Dict) -> Optional[datetime]:
        """Extract original timestamp from EXIF."""
        try:
            # DateTimeOriginal (36867) or DateTime (306)
            timestamp_str = exif_data.get(36867) or exif_data.get(306)
            if timestamp_str:
                # Format: "2024:01:15 14:30:00"
                return datetime.strptime(timestamp_str, "%Y:%m:%d %H:%M:%S").replace(tzinfo=timezone.utc)
            return None
        except:
            return None
    
    def _extract_device_info(self, exif_data: Dict) -> Optional[Dict[str, str]]:
        """Extract device make and model from EXIF."""
        try:
            make = exif_data.get(271)  # Make
            model = exif_data.get(272)  # Model
            
            if make or model:
                return {
                    "make": make or "Unknown",
                    "model": model or "Unknown"
                }
            return None
        except:
            return None
    
    def _haversine_distance(
        self,
        coord1: Tuple[float, float],
        coord2: Tuple[float, float]
    ) -> float:
        """
        Calculate distance between two GPS coordinates in kilometers.
        """
        R = 6371  # Earth's radius in km
        
        lat1, lon1 = math.radians(coord1[0]), math.radians(coord1[1])
        lat2, lon2 = math.radians(coord2[0]), math.radians(coord2[1])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
    
    async def _validate_gps_distance(
        self,
        image_coords: Tuple[float, float],
        pharmacy_id: str,
        claim_id: str
    ) -> float:
        """
        Validate distance between photo location and claimed pharmacy.
        
        Returns risk score contribution.
        """
        try:
            # Query pharmacy location
            from app.models.pharmacy import Pharmacy
            result = await self.db.execute(
                select(Pharmacy).where(Pharmacy.id == pharmacy_id)
            )
            pharmacy = result.scalar_one_or_none()
            
            if not pharmacy or not pharmacy.latitude or not pharmacy.longitude:
                logger.warning(f"Pharmacy location not found for claim {claim_id}")
                return 0.0
            
            pharmacy_coords = (pharmacy.latitude, pharmacy.longitude)
            distance = self._haversine_distance(image_coords, pharmacy_coords)
            
            logger.info(f"GPS distance for claim {claim_id}: {distance:.2f}km")
            
            # Log the check
            await self._log_fraud_check(
                claim_id,
                FraudCheckType.GPS_DISTANCE,
                FraudCheckResult.FAIL if distance > GPS_DISTANCE_THRESHOLD_KM else FraudCheckResult.PASS,
                min(1.0, distance / 100),
                {
                    "image_coords": image_coords,
                    "pharmacy_coords": pharmacy_coords,
                    "distance_km": distance
                }
            )
            
            if distance > GPS_DISTANCE_AUTO_REJECT_KM:
                return 1.0  # Auto-reject
            elif distance > GPS_DISTANCE_THRESHOLD_KM:
                return 0.3 * (distance / GPS_DISTANCE_AUTO_REJECT_KM)
            
            return 0.0
        except Exception as e:
            logger.error(f"Error validating GPS: {e}")
            return 0.0
    
    def _analyze_timestamp(
        self,
        exif_timestamp: datetime,
        submitted_at: datetime,
        claim_id: str
    ) -> float:
        """
        Analyze EXIF timestamp for stale or tampered photos.
        
        Returns risk score contribution.
        """
        try:
            # Ensure both timestamps are timezone-aware
            if exif_timestamp.tzinfo is None:
                exif_timestamp = exif_timestamp.replace(tzinfo=timezone.utc)
            if submitted_at.tzinfo is None:
                submitted_at = submitted_at.replace(tzinfo=timezone.utc)
            
            time_diff = submitted_at - exif_timestamp
            
            # Check for future timestamp (tampered)
            if time_diff.total_seconds() < 0:
                logger.warning(f"Future timestamp detected for claim {claim_id}")
                return 0.5
            
            # Check for stale image
            hours_old = time_diff.total_seconds() / 3600
            if hours_old > STALE_IMAGE_HOURS:
                logger.warning(f"Stale image detected for claim {claim_id}: {hours_old:.1f} hours old")
                return 0.2 * min(1.0, hours_old / (STALE_IMAGE_HOURS * 7))  # Cap at 1 week
            
            return 0.0
        except Exception as e:
            logger.error(f"Error analyzing timestamp: {e}")
            return 0.0
    
    def _detect_screenshot(self, image: Image.Image, exif_data: Dict) -> float:
        """
        Detect if image is a screenshot rather than a camera photo.
        
        Returns risk score contribution.
        """
        try:
            width, height = image.size
            aspect_ratio = width / height
            
            # Check for screenshot aspect ratios
            for w, h in SCREENSHOT_RATIOS:
                expected_ratio = w / h
                if abs(aspect_ratio - expected_ratio) < 0.01:
                    # Check for missing camera EXIF
                    if not exif_data.get(271) and not exif_data.get(272):  # Make/Model
                        logger.warning(f"Screenshot detected: aspect ratio {width}x{height}")
                        return 0.3
            
            return 0.0
        except Exception as e:
            logger.error(f"Error detecting screenshot: {e}")
            return 0.0
    
    async def _check_velocity(self, artisan_phone: str, claim_id: str) -> float:
        """
        Check claim velocity (frequency) for same artisan.
        
        Returns risk score contribution.
        """
        try:
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
            
            result = await self.db.execute(
                select(func.count(Claim.id)).where(
                    Claim.artisan_phone == artisan_phone,
                    Claim.submitted_at >= one_hour_ago,
                    Claim.id != claim_id
                )
            )
            recent_claims = result.scalar()
            
            if recent_claims > VELOCITY_CLAIM_LIMIT:
                logger.warning(f"Velocity exceeded for {artisan_phone}: {recent_claims} claims in 1 hour")
                await self._log_fraud_check(
                    claim_id,
                    FraudCheckType.VELOCITY,
                    FraudCheckResult.FAIL,
                    0.4,
                    {"recent_claims": recent_claims, "limit": VELOCITY_CLAIM_LIMIT}
                )
                return 0.4
            
            return 0.0
        except Exception as e:
            logger.error(f"Error checking velocity: {e}")
            return 0.0
    
    async def _log_fraud_check(
        self,
        claim_id: str,
        check_type: FraudCheckType,
        result: FraudCheckResult,
        confidence: float,
        metadata: Dict
    ):
        """Log fraud check to audit trail."""
        try:
            log = FraudLog(
                claim_id=claim_id,
                check_type=check_type,
                result=result,
                confidence=confidence,
                metadata=metadata
            )
            self.db.add(log)
            await self.db.commit()
        except Exception as e:
            logger.error(f"Error logging fraud check: {e}")
            await self.db.rollback()


class ImageDownloader:
    """Async image downloader from Backblaze B2."""
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
    
    async def download(self, url: str) -> bytes:
        """
        Download image from URL.
        
        Args:
            url: Backblaze B2 signed URL
        
        Returns:
            Raw image bytes
        
        Raises:
            aiohttp.ClientError: If download fails
            asyncio.TimeoutError: If download times out
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=self.timeout) as response:
                if response.status != 200:
                    raise aiohttp.ClientError(f"HTTP {response.status}")
                return await response.read()
