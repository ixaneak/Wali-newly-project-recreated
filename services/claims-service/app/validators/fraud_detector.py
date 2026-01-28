"""Fraud detection using perceptual hashing."""
from PIL import Image
import imagehash
from io import BytesIO
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class FraudDetector:
    """Detect duplicate claim images using perceptual hashing."""
    
    @staticmethod
    def calculate_phash(image_data: bytes) -> str:
        """
        Calculate perceptual hash (pHash) for an image.
        
        Args:
            image_data: Binary image data
        
        Returns:
            Hexadecimal hash string
        """
        try:
            image = Image.open(BytesIO(image_data))
            # Convert to grayscale for better hashing
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Calculate perceptual hash
            phash = imagehash.phash(image, hash_size=8)
            return str(phash)
        except Exception as e:
            logger.error(f"Error calculating pHash: {e}")
            raise ValueError(f"Failed to calculate image hash: {str(e)}")
    
    @staticmethod
    def check_duplicate_images(
        db: Session,
        phash: str,
        user_id: str,
        exclude_claim_id: str = None
    ) -> list[dict]:
        """
        Check if similar images exist in the database.
        
        Args:
            db: Database session
            phash: Perceptual hash of current image
            user_id: User ID to check across all users
            exclude_claim_id: Optional claim ID to exclude from search
        
        Returns:
            List of matching claims with similarity scores
        """
        from app.models.claim import Claim
        
        # Query all claims with image hashes
        # Note: We fetch all and process in Python to support MockDB and avoid complex array unnesting SQL
        query = db.query(Claim).filter(Claim.image_hashes != None)
        
        if exclude_claim_id:
            query = query.filter(Claim.id != exclude_claim_id)
            
        claims = query.all()
        
        matches = []
        current_hash = imagehash.hex_to_hash(phash)
        
        for claim in claims:
            if not claim.image_hashes:
                continue
                
            for stored_hash_str in claim.image_hashes:
                try:
                    stored_hash = imagehash.hex_to_hash(stored_hash_str)
                    
                    # Calculate Hamming distance
                    distance = current_hash - stored_hash
                    
                    # Check if within similarity threshold
                    if distance <= settings.phash_similarity_threshold:
                        matches.append({
                            "claim_id": str(claim.id),
                            "user_id": str(claim.user_id),
                            "claim_number": claim.claim_number,
                            "description": claim.description,
                            "similarity_score": distance,
                            "created_at": claim.created_at.isoformat() if claim.created_at else None,
                            "same_user": str(claim.user_id) == user_id
                        })
                        # Found a match in this claim, no need to check other images in same claim
                        # (or maybe we do? current logic implies we just need 'a' match. 
                        # Let's keep it simple: if any image in the claim matches, report the claim.)
                        # But wait, the original SQL unnested, so it produced 1 row per matching hash.
                        # Do we want multiple entries for the same claim if multiple images match?
                        # The original code:
                        # matches.append({...})
                        # AND then it returns 'matches'.
                        # The original SQL unnested, so `stored_hash` was a column.
                        # It returned 1 row per hash.
                        # So if a claim had 2 matching images, it appeared twice?
                        # Yes.
                        # However, for fraud detection, usually we just want to know if the claim is fraudulent.
                        # Let's stick to the behavior: one entry per matching image hash.
                        
                except Exception as e:
                    logger.warning(f"Error comparing hash {stored_hash_str}: {e}")
                    continue
        
        # Sort by similarity (lower distance = more similar)
        matches.sort(key=lambda x: x["similarity_score"])
        
        return matches
    
    @staticmethod
    def detect_fraud_patterns(matches: list[dict]) -> dict:
        """
        Analyze matches to detect fraud patterns.
        
        Args:
            matches: List of matching claims
        
        Returns:
            Fraud analysis report
        """
        if not matches:
            return {
                "fraud_detected": False,
                "risk_level": "low",
                "patterns": []
            }
        
        patterns = []
        risk_level = "low"
        
        # Pattern 1: Exact duplicate (distance = 0)
        exact_duplicates = [m for m in matches if m["similarity_score"] == 0]
        if exact_duplicates:
            patterns.append("Exact duplicate image found")
            risk_level = "critical"
        
        # Pattern 2: Same user reusing images
        same_user_matches = [m for m in matches if m["same_user"]]
        if len(same_user_matches) > 0:
            patterns.append(f"User has {len(same_user_matches)} similar previous claims")
            if risk_level == "low":
                risk_level = "medium"
        
        # Pattern 3: Multiple users with same image
        different_user_matches = [m for m in matches if not m["same_user"]]
        if len(different_user_matches) > 0:
            patterns.append(f"Image used by {len(different_user_matches)} other users")
            risk_level = "critical"
        
        # Pattern 4: Very similar images (distance 1-3)
        very_similar = [m for m in matches if 1 <= m["similarity_score"] <= 3]
        if len(very_similar) > 2:
            patterns.append(f"{len(very_similar)} very similar images detected")
            if risk_level != "critical":
                risk_level = "high"
        
        return {
            "fraud_detected": risk_level in ["high", "critical"],
            "risk_level": risk_level,
            "patterns": patterns,
            "match_count": len(matches),
            "exact_duplicates": len(exact_duplicates),
            "cross_user_matches": len(different_user_matches)
        }
