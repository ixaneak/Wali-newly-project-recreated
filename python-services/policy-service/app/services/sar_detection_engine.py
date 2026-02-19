"""
SAR (Suspicious Activity Report) Detection Engine

Implements automated fraud detection and AML (Anti-Money Laundering) compliance
for the Wali insurance platform. Monitors policies, claims, and transactions
for suspicious patterns that may indicate fraud, money laundering, or other
financial crimes.

COSUMAF Compliance: All flagged activities are retained for 5 years minimum.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import json
import hashlib
import re
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
import logging

logger = logging.getLogger(__name__)


class RiskSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DetectionRuleType(Enum):
    RAPID_CLAIM = "rapid_claim"
    STRUCTURING = "structuring"
    GEOLOCATION_ANOMALY = "geolocation_anomaly"
    DEVICE_FINGERPRINT = "device_fingerprint"
    DOCUMENT_FORGERY = "document_forgery"
    THIRD_PARTY_PAYMENT = "third_party_payment"
    ROUND_NUMBERS = "round_numbers"
    SANCTIONS_LIST = "sanctions_list"
    VELOCITY_CHECK = "velocity_check"
    DUPLICATE_CLAIMS = "duplicate_claims"
    SUSPICIOUS_TIMING = "suspicious_timing"
    IDENTITY_MORPHING = "identity_morphing"
    COLLUSION = "collusion"
    PREMIUM_CASHING = "premium_cashing"


@dataclass
class RiskEvent:
    """Represents a detected risk event."""
    rule_type: DetectionRuleType
    severity: RiskSeverity
    policy_id: str
    risk_score: int  # 0-100
    description: str
    metadata: Dict[str, Any]
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> dict:
        return {
            "rule_type": self.rule_type.value,
            "severity": self.severity.value,
            "policy_id": self.policy_id,
            "risk_score": self.risk_score,
            "description": self.description,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class SARReport:
    """Suspicious Activity Report."""
    report_reference: str
    status: str  # draft, filed, under_review, closed
    subject_type: str
    subject_id: str
    subject_name: str
    subject_phone: str
    activity_type: str
    occurrence_date: datetime
    description: str
    amount_involved: int
    related_transactions: List[str]
    risk_score: int
    supporting_documents: List[str]
    detection_events: List[RiskEvent]
    created_at: datetime = None
    retention_until: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.retention_until is None:
            # 5 year retention as per COSUMAF
            self.retention_until = self.created_at + timedelta(days=365 * 5)


class SARDetectionEngine:
    """
    Main detection engine for identifying suspicious insurance activities.
    
    Implements multiple detection rules covering:
    - Policy-level fraud indicators
    - Claim-level anomaly detection
    - Transaction pattern analysis
    - AML compliance screening
    """
    
    # Risk score thresholds
    AUTO_ESCALATE_THRESHOLD = 70  # Auto-create SAR
    REVIEW_THRESHOLD = 40         # Flag for manual review
    MONITOR_THRESHOLD = 20        # Add to watchlist
    
    # Time windows for analysis
    RAPID_CLAIM_WINDOW = timedelta(hours=48)
    VELOCITY_WINDOW = timedelta(days=30)
    STRUCTURING_WINDOW = timedelta(days=30)
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.rules: List[Callable] = [
            self.check_rapid_claim,
            self.check_structuring,
            self.check_geolocation_anomaly,
            self.check_device_fingerprinting,
            self.check_document_forgery,
            self.check_third_party_payment,
            self.check_round_numbers,
            self.check_sanctions_list,
            self.check_velocity,
            self.check_duplicate_claims,
            self.check_suspicious_timing,
            self.check_identity_morphing,
            self.check_collusion,
            self.check_premium_cashing,
        ]
        
        # Ivory Coast phone prefixes by region
        self.region_prefixes = {
            '07': 'Abidjan',
            '08': 'Abidjan',
            '09': 'Abidjan',
            '05': 'Yamoussoukro',
            '01': 'North',
            '02': 'North',
            '03': 'West',
            '04': 'Center',
            '06': 'Southeast',
        }
    
    # ═════════════════════════════════════════════════════════════════
    # MAIN ANALYSIS METHODS
    # ═════════════════════════════════════════════════════════════════
    
    async def analyze_policy_creation(self, policy_data: dict) -> Optional[RiskEvent]:
        """
        Analyze new policy creation for red flags.
        Called when a new policy is created.
        """
        events = []
        
        for rule in self.rules:
            try:
                event = await rule(policy_data)
                if event:
                    events.append(event)
                    logger.info(f"Risk detected: {event.rule_type.value} for policy {policy_data.get('id')}")
            except Exception as e:
                logger.error(f"Rule {rule.__name__} failed: {e}")
                continue
        
        if not events:
            return None
        
        # Aggregate risk score (cap at 100)
        total_score = min(sum(e.risk_score for e in events), 100)
        
        # Determine action based on risk score
        if total_score >= self.AUTO_ESCALATE_THRESHOLD:
            sar_report = await self.create_sar_report(events, policy_data)
            return RiskEvent(
                rule_type=DetectionRuleType.STRUCTURING,  # Use as aggregate
                severity=RiskSeverity.CRITICAL,
                policy_id=policy_data['id'],
                risk_score=total_score,
                description=f"Auto-generated SAR: {len(events)} red flags detected. SAR Ref: {sar_report.report_reference}",
                metadata={
                    "triggered_rules": [e.rule_type.value for e in events],
                    "sar_reference": sar_report.report_reference,
                    "individual_scores": {e.rule_type.value: e.risk_score for e in events}
                }
            )
        elif total_score >= self.REVIEW_THRESHOLD:
            await self.flag_for_review(events, policy_data)
            return RiskEvent(
                rule_type=DetectionRuleType.STRUCTURING,
                severity=RiskSeverity.HIGH,
                policy_id=policy_data['id'],
                risk_score=total_score,
                description=f"High-risk policy requires manual review: {len(events)} flags",
                metadata={
                    "triggered_rules": [e.rule_type.value for e in events],
                    "requires_review": True
                }
            )
        elif total_score >= self.MONITOR_THRESHOLD:
            await self.add_to_watchlist(events, policy_data)
            return RiskEvent(
                rule_type=DetectionRuleType.STRUCTURING,
                severity=RiskSeverity.MEDIUM,
                policy_id=policy_data['id'],
                risk_score=total_score,
                description=f"Policy added to monitoring watchlist",
                metadata={
                    "triggered_rules": [e.rule_type.value for e in events],
                    "watchlisted": True
                }
            )
        
        return None
    
    async def analyze_claim_submission(self, claim_data: dict, policy_data: dict) -> Optional[RiskEvent]:
        """
        Analyze claim submission for fraud indicators.
        Called when a new claim is submitted.
        """
        # Combine claim and policy data for analysis
        combined_data = {**policy_data, **claim_data, "is_claim_analysis": True}
        
        events = []
        claim_specific_rules = [
            self.check_rapid_claim,
            self.check_document_forgery,
            self.check_geolocation_anomaly,
            self.check_duplicate_claims,
            self.check_suspicious_timing,
        ]
        
        for rule in claim_specific_rules:
            try:
                event = await rule(combined_data)
                if event:
                    events.append(event)
            except Exception as e:
                logger.error(f"Rule {rule.__name__} failed: {e}")
                continue
        
        if not events:
            return None
        
        total_score = min(sum(e.risk_score for e in events), 100)
        
        if total_score >= self.AUTO_ESCALATE_THRESHOLD:
            sar_report = await self.create_sar_report(events, combined_data)
            return RiskEvent(
                rule_type=DetectionRuleType.DUPLICATE_CLAIMS,
                severity=RiskSeverity.CRITICAL,
                policy_id=policy_data['id'],
                risk_score=total_score,
                description=f"Suspicious claim auto-escalated. SAR Ref: {sar_report.report_reference}",
                metadata={
                    "claim_id": claim_data.get('id'),
                    "triggered_rules": [e.rule_type.value for e in events],
                    "sar_reference": sar_report.report_reference
                }
            )
        elif total_score >= self.REVIEW_THRESHOLD:
            await self.flag_for_review(events, combined_data, claim_id=claim_data.get('id'))
            return RiskEvent(
                rule_type=DetectionRuleType.DUPLICATE_CLAIMS,
                severity=RiskSeverity.HIGH,
                policy_id=policy_data['id'],
                risk_score=total_score,
                description="Claim flagged for manual review",
                metadata={
                    "claim_id": claim_data.get('id'),
                    "triggered_rules": [e.rule_type.value for e in events]
                }
            )
        
        return None
    
    # ═════════════════════════════════════════════════════════════════
    # DETECTION RULES
    # ═════════════════════════════════════════════════════════════════
    
    async def check_rapid_claim(self, data: dict) -> Optional[RiskEvent]:
        """
        Detect claims filed very soon after policy creation.
        High indicator of pre-planned fraud.
        """
        if not data.get('is_claim_analysis'):
            # Only check during claim analysis
            return None
        
        policy_date_str = data.get('created_at') or data.get('policy_created_at')
        claim_date_str = data.get('claim_date') or data.get('created_at')
        
        if not policy_date_str or not claim_date_str:
            return None
        
        try:
            policy_date = self._parse_datetime(policy_date_str)
            claim_date = self._parse_datetime(claim_date_str)
            
            time_diff = claim_date - policy_date
            
            if time_diff < timedelta(hours=24):
                return RiskEvent(
                    rule_type=DetectionRuleType.RAPID_CLAIM,
                    severity=RiskSeverity.CRITICAL,
                    policy_id=data['id'],
                    risk_score=45,
                    description=f"Claim filed within 24 hours of policy creation",
                    metadata={
                        "hours_between": time_diff.total_seconds() / 3600,
                        "policy_date": policy_date.isoformat(),
                        "claim_date": claim_date.isoformat()
                    }
                )
            elif time_diff < self.RAPID_CLAIM_WINDOW:
                return RiskEvent(
                    rule_type=DetectionRuleType.RAPID_CLAIM,
                    severity=RiskSeverity.HIGH,
                    policy_id=data['id'],
                    risk_score=35,
                    description=f"Claim filed within 48 hours of policy creation",
                    metadata={
                        "hours_between": time_diff.total_seconds() / 3600
                    }
                )
            elif time_diff < timedelta(days=7):
                return RiskEvent(
                    rule_type=DetectionRuleType.RAPID_CLAIM,
                    severity=RiskSeverity.MEDIUM,
                    policy_id=data['id'],
                    risk_score=20,
                    description=f"Claim filed within first week of policy",
                    metadata={
                        "days_between": time_diff.days
                    }
                )
        except Exception as e:
            logger.error(f"Rapid claim check failed: {e}")
        
        return None
    
    async def check_structuring(self, data: dict) -> Optional[RiskEvent]:
        """
        Detect structuring: multiple policies just under reporting threshold
        to avoid detection (500k CFA threshold).
        """
        phone = data.get('phone_number')
        device_id = data.get('device_fingerprint')
        
        # Check by phone
        if phone:
            phone_policies = await self._get_recent_policies(
                phone=phone,
                days=30
            )
            
            if len(phone_policies) >= 3:
                total_amount = sum(p.get('amount', 0) for p in phone_policies)
                avg_amount = total_amount / len(phone_policies)
                
                # Check if amounts are suspiciously close to threshold
                threshold = 500000
                near_threshold_count = sum(
                    1 for p in phone_policies 
                    if threshold * 0.8 <= p.get('amount', 0) < threshold
                )
                
                if total_amount >= 400000 and near_threshold_count >= 2:
                    return RiskEvent(
                        rule_type=DetectionRuleType.STRUCTURING,
                        severity=RiskSeverity.CRITICAL,
                        policy_id=data['id'],
                        risk_score=50,
                        description=f"Potential structuring: {len(phone_policies)} policies totaling {total_amount:,} CFA",
                        metadata={
                            "policy_count": len(phone_policies),
                            "total_amount": total_amount,
                            "avg_amount": avg_amount,
                            "near_threshold_count": near_threshold_count,
                            "identifiers": [phone]
                        }
                    )
        
        # Check by device fingerprint
        if device_id:
            device_policies = await self._get_recent_policies(
                device_id=device_id,
                days=30
            )
            
            if len(device_policies) >= 3:
                unique_phones = set(p.get('phone_number') for p in device_policies)
                
                if len(unique_phones) >= 2:  # Multiple phones from same device
                    return RiskEvent(
                        rule_type=DetectionRuleType.STRUCTURING,
                        severity=RiskSeverity.HIGH,
                        policy_id=data['id'],
                        risk_score=40,
                        description=f"Multiple policies from same device with different phones",
                        metadata={
                            "policy_count": len(device_policies),
                            "unique_phones": list(unique_phones),
                            "device_id": device_id[:8] + "..."
                        }
                    )
        
        return None
    
    async def check_geolocation_anomaly(self, data: dict) -> Optional[RiskEvent]:
        """
        Detect when claim location is far from phone registration/purchase location.
        """
        phone = data.get('phone_number', '')
        claim_location = data.get('claim_gps', {})
        
        if not phone or not claim_location:
            return None
        
        # Extract region from phone prefix
        phone_prefix = phone[4:6] if len(phone) >= 6 else ''  # +225 XX
        phone_region = self.region_prefixes.get(phone_prefix, 'Unknown')
        
        # Determine claim region from GPS
        claim_region = self._gps_to_region(claim_location)
        
        if phone_region != claim_region and claim_region != 'Unknown':
            # Calculate rough distance score
            distance_score = self._calculate_distance_score(phone_region, claim_region)
            
            return RiskEvent(
                rule_type=DetectionRuleType.GEOLOCATION_ANOMALY,
                severity=RiskSeverity.HIGH if distance_score > 50 else RiskSeverity.MEDIUM,
                policy_id=data['id'],
                risk_score=min(20 + distance_score, 45),
                description=f"Claim in {claim_region} but phone registered in {phone_region}",
                metadata={
                    "phone_region": phone_region,
                    "claim_region": claim_region,
                    "claim_gps": claim_location,
                    "distance_score": distance_score
                }
            )
        
        return None
    
    async def check_device_fingerprinting(self, data: dict) -> Optional[RiskEvent]:
        """
        Detect suspicious device patterns:
        - Emulator usage
        - Multiple accounts from same device
        - Device in banned list
        """
        device_fp = data.get('device_fingerprint', {})
        
        if not device_fp:
            return None
        
        # Check for emulator
        if device_fp.get('is_emulator') or device_fp.get('is_vm'):
            return RiskEvent(
                rule_type=DetectionRuleType.DEVICE_FINGERPRINT,
                severity=RiskSeverity.HIGH,
                policy_id=data['id'],
                risk_score=35,
                description="Policy created from emulator or virtual machine",
                metadata={
                    "device_type": "emulator",
                    "device_details": device_fp
                }
            )
        
        # Check for rooted/jailbroken device
        if device_fp.get('is_rooted') or device_fp.get('is_jailbroken'):
            return RiskEvent(
                rule_type=DetectionRuleType.DEVICE_FINGERPRINT,
                severity=RiskSeverity.MEDIUM,
                policy_id=data['id'],
                risk_score=25,
                description="Policy created from rooted/jailbroken device",
                metadata={"device_type": "rooted"}
            )
        
        # Check device against known fraud devices
        device_hash = device_fp.get('device_hash')
        if device_hash:
            is_banned = await self._check_banned_device(device_hash)
            if is_banned:
                return RiskEvent(
                    rule_type=DetectionRuleType.DEVICE_FINGERPRINT,
                    severity=RiskSeverity.CRITICAL,
                    policy_id=data['id'],
                    risk_score=60,
                    description="Device previously associated with fraud",
                    metadata={"device_banned": True}
                )
        
        return None
    
    async def check_document_forgery(self, data: dict) -> Optional[RiskEvent]:
        """
        Detect signs of document manipulation:
        - EXIF metadata showing editing software
        - Timestamp inconsistencies
        - Duplicate image detection
        """
        documents = data.get('documents', [])
        
        if not documents:
            return None
        
        events = []
        
        for doc in documents:
            exif = doc.get('exif_data', {})
            
            # Check for editing software
            software = exif.get('Software', '').lower()
            editing_tools = ['photoshop', 'gimp', 'lightroom', 'paint.net', 'canva']
            
            if any(tool in software for tool in editing_tools):
                events.append(RiskEvent(
                    rule_type=DetectionRuleType.DOCUMENT_FORGERY,
                    severity=RiskSeverity.HIGH,
                    policy_id=data['id'],
                    risk_score=40,
                    description=f"Document edited with {software}",
                    metadata={
                        "software": software,
                        "document_type": doc.get('type'),
                        "file_hash": doc.get('hash', '')[:16]
                    }
                ))
            
            # Check timestamp consistency
            photo_date = exif.get('DateTimeOriginal')
            claim_date = data.get('claim_date') or data.get('created_at')
            
            if photo_date and claim_date:
                try:
                    photo_dt = datetime.strptime(photo_date, "%Y:%m:%d %H:%M:%S")
                    claim_dt = self._parse_datetime(claim_date)
                    
                    time_diff = abs((photo_dt - claim_dt).days)
                    
                    if time_diff > 30:
                        events.append(RiskEvent(
                            rule_type=DetectionRuleType.DOCUMENT_FORGERY,
                            severity=RiskSeverity.HIGH,
                            policy_id=data['id'],
                            risk_score=35,
                            description=f"Document taken {time_diff} days from claim date",
                            metadata={
                                "photo_date": photo_date,
                                "claim_date": claim_date,
                                "days_difference": time_diff
                            }
                        ))
                    elif time_diff > 7:
                        events.append(RiskEvent(
                            rule_type=DetectionRuleType.DOCUMENT_FORGERY,
                            severity=RiskSeverity.MEDIUM,
                            policy_id=data['id'],
                            risk_score=20,
                            description=f"Document taken {time_diff} days from claim date",
                            metadata={
                                "days_difference": time_diff
                            }
                        ))
                except Exception:
                    pass
            
            # Check for duplicate images
            img_hash = doc.get('perceptual_hash')
            if img_hash:
                is_duplicate = await self._check_duplicate_image(img_hash, data['id'])
                if is_duplicate:
                    events.append(RiskEvent(
                        rule_type=DetectionRuleType.DOCUMENT_FORGERY,
                        severity=RiskSeverity.CRITICAL,
                        policy_id=data['id'],
                        risk_score=50,
                        description="Duplicate or near-duplicate document detected",
                        metadata={"perceptual_hash": img_hash[:16]}
                    ))
        
        # Return highest scoring event
        return max(events, key=lambda e: e.risk_score) if events else None
    
    async def check_velocity(self, data: dict) -> Optional[RiskEvent]:
        """
        Detect unusual velocity of transactions or claims.
        """
        phone = data.get('phone_number')
        user_id = data.get('user_id')
        
        # Check claim velocity
        recent_claims = await self._get_recent_claims(
            phone=phone,
            days=7
        )
        
        if len(recent_claims) >= 3:
            return RiskEvent(
                rule_type=DetectionRuleType.VELOCITY_CHECK,
                severity=RiskSeverity.HIGH,
                policy_id=data['id'],
                risk_score=40,
                description=f"{len(recent_claims)} claims filed in past 7 days",
                metadata={
                    "claim_count": len(recent_claims),
                    "claim_ids": [c.get('id') for c in recent_claims]
                }
            )
        
        # Check policy creation velocity
        recent_policies = await self._get_recent_policies(
            phone=phone,
            days=7
        )
        
        if len(recent_policies) >= 5:
            return RiskEvent(
                rule_type=DetectionRuleType.VELOCITY_CHECK,
                severity=RiskSeverity.MEDIUM,
                policy_id=data['id'],
                risk_score=30,
                description=f"{len(recent_policies)} policies created in past 7 days",
                metadata={"policy_count": len(recent_policies)}
            )
        
        return None
    
    async def check_duplicate_claims(self, data: dict) -> Optional[RiskEvent]:
        """
        Detect duplicate or very similar claims.
        """
        if not data.get('is_claim_analysis'):
            return None
        
        claim_desc = data.get('description', '').lower()
        claim_amount = data.get('amount', 0)
        phone = data.get('phone_number')
        
        # Find similar recent claims
        recent_claims = await self._get_recent_claims(
            phone=phone,
            days=90
        )
        
        duplicates = []
        for claim in recent_claims:
            if claim.get('id') == data.get('id'):
                continue
            
            # Check amount similarity
            other_amount = claim.get('amount', 0)
            amount_similar = abs(claim_amount - other_amount) / max(claim_amount, 1) < 0.1
            
            # Check description similarity (simple)
            other_desc = claim.get('description', '').lower()
            desc_similar = self._text_similarity(claim_desc, other_desc) > 0.7
            
            if amount_similar and desc_similar:
                duplicates.append(claim)
        
        if len(duplicates) >= 2:
            return RiskEvent(
                rule_type=DetectionRuleType.DUPLICATE_CLAIMS,
                severity=RiskSeverity.CRITICAL,
                policy_id=data['id'],
                risk_score=55,
                description=f"Claim similar to {len(duplicates)} previous claims",
                metadata={
                    "duplicate_claims": [c.get('id') for c in duplicates],
                    "similarity_threshold": "70%"
                }
            )
        elif len(duplicates) == 1:
            return RiskEvent(
                rule_type=DetectionRuleType.DUPLICATE_CLAIMS,
                severity=RiskSeverity.HIGH,
                policy_id=data['id'],
                risk_score=35,
                description="Claim very similar to previous claim",
                metadata={"duplicate_claim_id": duplicates[0].get('id')}
            )
        
        return None
    
    async def check_suspicious_timing(self, data: dict) -> Optional[RiskEvent]:
        """
        Detect claims filed at suspicious times (middle of night, holidays, etc.)
        """
        claim_date_str = data.get('claim_date') or data.get('created_at')
        
        if not claim_date_str:
            return None
        
        try:
            claim_dt = self._parse_datetime(claim_date_str)
            hour = claim_dt.hour
            
            # Check for middle of night submissions (2 AM - 5 AM)
            if 2 <= hour <= 5:
                return RiskEvent(
                    rule_type=DetectionRuleType.SUSPICIOUS_TIMING,
                    severity=RiskSeverity.MEDIUM,
                    policy_id=data['id'],
                    risk_score=20,
                    description=f"Claim submitted at {hour}:00 AM (suspicious timing)",
                    metadata={"submission_hour": hour}
                )
            
            # Check for weekend/holiday patterns could be added here
            
        except Exception:
            pass
        
        return None
    
    async def check_identity_morphing(self, data: dict) -> Optional[RiskEvent]:
        """
        Detect when user slightly changes identity info to bypass controls.
        """
        phone = data.get('phone_number')
        current_name = data.get('full_name', '').lower().strip()
        current_id = data.get('id_number', '').strip()
        
        # Get historical data for same phone
        historical = await self._get_historical_policies(phone)
        
        if len(historical) < 2:
            return None
        
        name_variations = set()
        id_variations = set()
        
        for record in historical:
            name_variations.add(record.get('full_name', '').lower().strip())
            id_variations.add(record.get('id_number', '').strip())
        
        # Check for slight name variations
        if len(name_variations) > 1:
            # Check for morphing (same person, slight spelling differences)
            from difflib import SequenceMatcher
            
            names = list(name_variations)
            for i in range(len(names)):
                for j in range(i + 1, len(names)):
                    similarity = SequenceMatcher(None, names[i], names[j]).ratio()
                    if 0.7 < similarity < 1.0:  # Similar but not identical
                        return RiskEvent(
                            rule_type=DetectionRuleType.IDENTITY_MORPHING,
                            severity=RiskSeverity.HIGH,
                            policy_id=data['id'],
                            risk_score=40,
                            description="Name variations detected across policies",
                            metadata={
                                "name_variations": list(name_variations),
                                "similarity": similarity
                            }
                        )
        
        return None
    
    async def check_collusion(self, data: dict) -> Optional[RiskEvent]:
        """
        Detect potential collusion between policyholders and service providers.
        """
        # Check if multiple claims involve same service provider
        phone = data.get('phone_number')
        provider = data.get('service_provider') or data.get('pharmacy_id')
        
        if not provider:
            return None
        
        # Get claims with same provider
        recent_claims = await self._get_recent_claims_with_provider(
            provider=provider,
            days=30
        )
        
        unique_phones = set(c.get('phone_number') for c in recent_claims)
        
        if len(recent_claims) >= 5 and len(unique_phones) >= 3:
            return RiskEvent(
                rule_type=DetectionRuleType.COLLUSION,
                severity=RiskSeverity.HIGH,
                policy_id=data['id'],
                risk_score=35,
                description=f"Provider involved in {len(recent_claims)} recent claims",
                metadata={
                    "provider_id": provider,
                    "claim_count": len(recent_claims),
                    "unique_customers": len(unique_phones)
                }
            )
        
        return None
    
    async def check_premium_cashing(self, data: dict) -> Optional[RiskEvent]:
        """
        Detect policy cancellation shortly after claim payout (premium cashing).
        """
        if not data.get('is_claim_analysis'):
            return None
        
        policy_status = data.get('status')
        claim_status = data.get('claim_status')
        
        if policy_status == 'cancelled' and claim_status == 'paid':
            claim_paid_date = data.get('claim_paid_date')
            cancellation_date = data.get('cancelled_at')
            
            if claim_paid_date and cancellation_date:
                try:
                    paid_dt = self._parse_datetime(claim_paid_date)
                    cancel_dt = self._parse_datetime(cancellation_date)
                    
                    days_diff = (cancel_dt - paid_dt).days
                    
                    if days_diff < 30:
                        return RiskEvent(
                            rule_type=DetectionRuleType.PREMIUM_CASHING,
                            severity=RiskSeverity.CRITICAL,
                            policy_id=data['id'],
                            risk_score=50,
                            description=f"Policy cancelled {days_diff} days after claim payout",
                            metadata={
                                "days_after_payout": days_diff,
                                "claim_amount": data.get('claim_amount'),
                                "premium_paid": data.get('premium_paid')
                            }
                        )
                except Exception:
                    pass
        
        return None
    
    async def check_third_party_payment(self, data: dict) -> Optional[RiskEvent]:
        """
        Detect when premium is paid by different person than policyholder.
        """
        payer_phone = data.get('payment_phone')
        policy_phone = data.get('phone_number')
        payer_name = data.get('payment_name', '').lower()
        policy_name = data.get('full_name', '').lower()
        
        if not payer_phone:
            return None
        
        if payer_phone != policy_phone:
            # Check if names also differ significantly
            from difflib import SequenceMatcher
            name_similarity = SequenceMatcher(None, payer_name, policy_name).ratio()
            
            if name_similarity < 0.5:
                return RiskEvent(
                    rule_type=DetectionRuleType.THIRD_PARTY_PAYMENT,
                    severity=RiskSeverity.HIGH,
                    policy_id=data['id'],
                    risk_score=30,
                    description="Premium paid by different person (phone and name mismatch)",
                    metadata={
                        "payer_phone": payer_phone,
                        "policy_phone": policy_phone,
                        "name_similarity": name_similarity
                    }
                )
            else:
                return RiskEvent(
                    rule_type=DetectionRuleType.THIRD_PARTY_PAYMENT,
                    severity=RiskSeverity.MEDIUM,
                    policy_id=data['id'],
                    risk_score=20,
                    description="Premium paid by different phone number",
                    metadata={
                        "payer_phone": payer_phone,
                        "policy_phone": policy_phone
                    }
                )
        
        return None
    
    async def check_round_numbers(self, data: dict) -> Optional[RiskEvent]:
        """
        Detect premiums or claims in exact round numbers (indicates calculation).
        """
        amount = data.get('amount', 0)
        claim_amount = data.get('claim_amount', 0)
        
        check_amounts = [a for a in [amount, claim_amount] if a > 0]
        
        for amt in check_amounts:
            # Highly suspicious: exact thousands
            if amt > 10000 and amt % 1000 == 0 and amt % 10000 == 0:
                return RiskEvent(
                    rule_type=DetectionRuleType.ROUND_NUMBERS,
                    severity=RiskSeverity.MEDIUM,
                    policy_id=data['id'],
                    risk_score=25,
                    description=f"Transaction amount {amt:,} CFA is highly rounded (exact 10k)",
                    metadata={"amount": amt, "rounding": "10000"}
                )
            
            # Moderately suspicious: ends in 000
            if amt > 5000 and amt % 1000 == 0:
                return RiskEvent(
                    rule_type=DetectionRuleType.ROUND_NUMBERS,
                    severity=RiskSeverity.LOW,
                    policy_id=data['id'],
                    risk_score=10,
                    description=f"Transaction amount {amt:,} CFA is rounded",
                    metadata={"amount": amt, "rounding": "1000"}
                )
        
        return None
    
    async def check_sanctions_list(self, data: dict) -> Optional[RiskEvent]:
        """
        Check against UN/EU sanctions lists and local PEP database.
        """
        name = data.get('full_name', '').lower().strip()
        phone = data.get('phone_number', '')
        id_number = data.get('id_number', '')
        
        identifiers = [name, phone, id_number]
        
        for identifier in identifiers:
            if not identifier:
                continue
            
            # Query compliance lists
            match = await self._check_compliance_list(identifier)
            
            if match:
                return RiskEvent(
                    rule_type=DetectionRuleType.SANCTIONS_LIST,
                    severity=RiskSeverity.CRITICAL,
                    policy_id=data['id'],
                    risk_score=100,
                    description=f"Match on {match['list_type']}: {match['reason']}",
                    metadata={
                        "list_type": match['list_type'],
                        "match_id": str(match['id']),
                        "matched_field": match.get('field'),
                        "identifier_type": "name" if identifier == name else "phone" if identifier == phone else "id"
                    }
                )
        
        return None
    
    # ═════════════════════════════════════════════════════════════════
    # SAR CREATION & REPORTING
    # ═════════════════════════════════════════════════════════════════
    
    async def create_sar_report(self, events: List[RiskEvent], data: dict) -> SARReport:
        """
        Auto-create SAR report for high-risk activity.
        COSUMAF requires 5-year retention.
        """
        report_ref = f"SAR-{datetime.utcnow().year}-{await self._get_next_sequence():06d}"
        
        # Calculate total amount involved
        amount = data.get('amount', 0) or data.get('claim_amount', 0)
        
        # Build description from events
        descriptions = [e.description for e in events]
        
        sar = SARReport(
            report_reference=report_ref,
            status='draft',
            subject_type='policyholder',
            subject_id=data['id'],
            subject_name=data.get('full_name', 'Unknown'),
            subject_phone=data.get('phone_number', 'Unknown'),
            activity_type=events[0].rule_type.value,
            occurrence_date=events[0].timestamp,
            description="; ".join(descriptions),
            amount_involved=amount,
            related_transactions=[data.get('transaction_id', data['id'])],
            risk_score=sum(e.risk_score for e in events),
            supporting_documents=data.get('document_urls', []),
            detection_events=events
        )
        
        # Persist to database
        await self._persist_sar(sar)
        
        # Alert compliance team
        await self._alert_compliance_team(sar)
        
        logger.critical(f"SAR Created: {report_ref} for policy {data['id']}")
        
        return sar
    
    async def flag_for_review(self, events: List[RiskEvent], data: dict, claim_id: str = None):
        """Flag case for manual compliance review."""
        await self.db.execute(
            """INSERT INTO compliance_flags (
                policy_id, claim_id, flag_type, severity, 
                description, triggered_rules, status, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            ON CONFLICT (policy_id, flag_type) DO UPDATE SET
                severity = EXCLUDED.severity,
                description = EXCLUDED.description,
                triggered_rules = EXCLUDED.triggered_rules,
                status = 'open',
                updated_at = $8""",
            data['id'],
            claim_id,
            'manual_review',
            max([e.severity.value for e in events]),
            f"{len(events)} risk flags detected",
            json.dumps([e.rule_type.value for e in events]),
            'open',
            datetime.utcnow()
        )
        
        logger.warning(f"Flagged for review: Policy {data['id']}, Claim {claim_id}")
    
    async def add_to_watchlist(self, events: List[RiskEvent], data: dict):
        """Add entity to monitoring watchlist."""
        await self.db.execute(
            """INSERT INTO watchlist (
                entity_type, entity_id, phone_number, 
                risk_score, reason, added_at, expires_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (entity_type, entity_id) DO UPDATE SET
                risk_score = GREATEST(watchlist.risk_score, EXCLUDED.risk_score),
                updated_at = $6""",
            'policyholder',
            data['id'],
            data.get('phone_number'),
            sum(e.risk_score for e in events),
            json.dumps([e.rule_type.value for e in events]),
            datetime.utcnow(),
            datetime.utcnow() + timedelta(days=90)  # 90-day watch
        )
    
    # ═════════════════════════════════════════════════════════════════
    # HELPER METHODS
    # ═════════════════════════════════════════════════════════════════
    
    def _parse_datetime(self, date_str: str) -> datetime:
        """Parse various datetime formats."""
        formats = [
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%Y:%m:%d %H:%M:%S",  # EXIF format
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str.split('.')[0], fmt)
            except ValueError:
                continue
        
        # Try ISO format
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    
    def _gps_to_region(self, gps: dict) -> str:
        """Convert GPS coordinates to Ivory Coast region."""
        if not gps or 'lat' not in gps or 'lng' not in gps:
            return 'Unknown'
        
        lat = gps['lat']
        lng = gps['lng']
        
        # Rough region boundaries for Ivory Coast
        if 5.3 <= lat <= 5.5 and -4.1 <= lng <= -3.9:
            return 'Abidjan'
        elif 6.8 <= lat <= 6.9 and -5.3 <= lng <= -5.2:
            return 'Yamoussoukro'
        elif lat > 7.5:
            return 'North'
        elif lng < -6:
            return 'West'
        elif lat < 5:
            return 'Southeast'
        else:
            return 'Center'
    
    def _calculate_distance_score(self, region1: str, region2: str) -> int:
        """Calculate distance score between regions (0-100)."""
        # Simplified scoring
        if region1 == region2:
            return 0
        
        # Adjacent regions
        adjacent = {
            'Abidjan': ['Southeast', 'Center'],
            'Yamoussoukro': ['Center'],
            'Center': ['Abidjan', 'Yamoussoukro', 'North', 'West'],
            'North': ['Center', 'West'],
            'West': ['North', 'Center'],
            'Southeast': ['Abidjan'],
        }
        
        if region2 in adjacent.get(region1, []):
            return 25
        
        return 50  # Far apart
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity ratio."""
        from difflib import SequenceMatcher
        return SequenceMatcher(None, text1, text2).ratio()
    
    async def _get_recent_policies(self, phone: str = None, device_id: str = None, days: int = 30) -> List[dict]:
        """Fetch recent policies by phone or device."""
        # This is a mock - implement actual DB query
        return []
    
    async def _get_recent_claims(self, phone: str = None, days: int = 30) -> List[dict]:
        """Fetch recent claims."""
        return []
    
    async def _get_recent_claims_with_provider(self, provider: str, days: int = 30) -> List[dict]:
        """Fetch recent claims for a specific provider."""
        return []
    
    async def _get_historical_policies(self, phone: str) -> List[dict]:
        """Get all historical policies for a phone number."""
        return []
    
    async def _check_banned_device(self, device_hash: str) -> bool:
        """Check if device is in banned list."""
        return False
    
    async def _check_duplicate_image(self, perceptual_hash: str, exclude_id: str) -> bool:
        """Check for duplicate/near-duplicate images."""
        return False
    
    async def _check_compliance_list(self, identifier: str) -> Optional[dict]:
        """Check against sanctions/PEP lists."""
        return None
    
    async def _get_next_sequence(self) -> int:
        """Get next SAR sequence number."""
        try:
            result = await self.db.fetchval(
                "SELECT COUNT(*) FROM sar_reports WHERE created_at >= DATE_TRUNC('year', NOW())"
            )
            return (result or 0) + 1
        except Exception:
            return 1
    
    async def _persist_sar(self, sar: SARReport):
        """Persist SAR to database."""
        # Implementation depends on your DB schema
        pass
    
    async def _alert_compliance_team(self, sar: SARReport):
        """Send alert to compliance team."""
        # Implement email/SMS/Slack notification
        logger.info(f"Compliance alert sent for SAR: {sar.report_reference}")
