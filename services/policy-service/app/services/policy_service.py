"""Policy service business logic."""
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.policy import Policy, PolicyStatus, CoverageType, PaymentFrequency
from app.core.config import get_settings

settings = get_settings()


class PremiumCalculator:
    """Calculate insurance premiums based on coverage type."""
    
    PREMIUM_RANGES = {
        CoverageType.HEALTH: (100, 200),      # XOF 100-200/day
        CoverageType.EQUIPMENT: (150, 300),   # XOF 150-300/day
        CoverageType.THEFT: (200, 500),       # XOF 200-500/day
        CoverageType.BUNDLE: (300, 500),      # XOF 300-500/day
    }
    
    @classmethod
    def calculate_daily_premium(
        cls, 
        coverage_type: CoverageType, 
        coverage_amount: int,
        risk_factors: Optional[dict] = None
    ) -> int:
        """
        Calculate daily premium based on coverage type and amount.
        
        Args:
            coverage_type: Type of coverage
            coverage_amount: Maximum coverage amount in XOF
            risk_factors: Optional dict with region, profession, etc.
        
        Returns:
            Daily premium in XOF (as integer)
        """
        min_premium, max_premium = cls.PREMIUM_RANGES[coverage_type]
        
        # Base premium is proportional to coverage amount
        # Example: XOF 50,000 coverage = XOF 150/day for health
        base_rate = 0.003  # 0.3% per day
        calculated = int(coverage_amount * base_rate)
        
        # Clamp to valid range
        premium = max(min_premium, min(calculated, max_premium))
        
        # Apply risk factors
        if risk_factors:
            region = risk_factors.get("region", "")
            # Higher risk in certain regions
            if region in ["Abidjan", "San-Pédro"]:
                premium = int(premium * 1.1)
        
        return premium
    
    @classmethod
    def calculate_next_payment_date(
        cls, 
        frequency: PaymentFrequency, 
        from_date: Optional[datetime] = None
    ) -> datetime:
        """Calculate next payment date based on frequency."""
        base_date = from_date or datetime.now()
        
        if frequency == PaymentFrequency.DAILY:
            return base_date + timedelta(days=1)
        elif frequency == PaymentFrequency.WEEKLY:
            return base_date + timedelta(weeks=1)
        elif frequency == PaymentFrequency.MONTHLY:
            # Add roughly 30 days for monthly
            return base_date + timedelta(days=30)
        
        return base_date


class PolicyService:
    """Service for managing insurance policies."""
    
    @staticmethod
    def create_policy(
        db: Session,
        user_id: str,
        coverage_type: CoverageType,
        coverage_details: dict,
        payment_frequency: PaymentFrequency,
        region: Optional[str] = None
    ) -> Policy:
        """
        Create a new insurance policy.
        
        Args:
            db: Database session
            user_id: User UUID
            coverage_type: Type of coverage
            coverage_details: Dict with coverage specifics (max_amount, etc.)
            payment_frequency: How often to pay premiums
            region: User region for risk calculation
        
        Returns:
            Created Policy object
        """
        # Calculate premium
        coverage_amount = coverage_details.get("max_coverage_amount", 50000)
        risk_factors = {"region": region} if region else None
        
        daily_premium = PremiumCalculator.calculate_daily_premium(
            coverage_type, 
            coverage_amount, 
            risk_factors
        )
        
        # Adjust for payment frequency
        if payment_frequency == PaymentFrequency.DAILY:
            premium_amount = daily_premium
        elif payment_frequency == PaymentFrequency.WEEKLY:
            premium_amount = daily_premium * 7
        else:  # MONTHLY
            premium_amount = daily_premium * 30
        
        # Create policy
        policy = Policy(
            user_id=user_id,
            coverage_type=coverage_type,
            coverage_details=coverage_details,
            premium_amount=premium_amount,
            payment_frequency=payment_frequency,
            status=PolicyStatus.PENDING
        )
        
        try:
            db.add(policy)
            db.commit()
            db.refresh(policy)
            return policy
        except IntegrityError:
            db.rollback()
            raise ValueError("Failed to create policy")
    
    @staticmethod
    def activate_policy(db: Session, policy_id: str, transaction_ref: str) -> Policy:
        """Activate a policy after successful payment."""
        policy = db.query(Policy).filter(Policy.id == policy_id).first()
        if not policy:
            raise ValueError("Policy not found")
        
        policy.status = PolicyStatus.ACTIVE
        policy.mobile_money_ref = transaction_ref
        policy.start_date = datetime.now()
        policy.last_payment_date = datetime.now()
        policy.next_payment_date = PremiumCalculator.calculate_next_payment_date(
            policy.payment_frequency
        )
        
        db.commit()
        db.refresh(policy)
        return policy
    
    @staticmethod
    def get_user_policies(db: Session, user_id: str, status: Optional[PolicyStatus] = None):
        """Get all policies for a user."""
        query = db.query(Policy).filter(Policy.user_id == user_id)
        
        if status:
            query = query.filter(Policy.status == status)
        
        return query.order_by(Policy.created_at.desc()).all()
    
    @staticmethod
    def get_policy(db: Session, policy_id: str) -> Optional[Policy]:
        """Get a single policy by ID."""
        return db.query(Policy).filter(Policy.id == policy_id).first()
    
    @staticmethod
    def update_policy_payment(
        db: Session, 
        policy_id: str, 
        transaction_ref: str
    ) -> Policy:
        """Update policy after premium payment."""
        policy = db.query(Policy).filter(Policy.id == policy_id).first()
        if not policy:
            raise ValueError("Policy not found")
        
        policy.last_payment_date = datetime.now()
        policy.next_payment_date = PremiumCalculator.calculate_next_payment_date(
            policy.payment_frequency,
            from_date=datetime.now()
        )
        policy.mobile_money_ref = transaction_ref
        
        db.commit()
        db.refresh(policy)
        return policy
    
    @staticmethod
    def cancel_policy(
        db: Session, 
        policy_id: str, 
        reason: str
    ) -> Policy:
        """Cancel a policy."""
        policy = db.query(Policy).filter(Policy.id == policy_id).first()
        if not policy:
            raise ValueError("Policy not found")
        
        policy.status = PolicyStatus.CANCELLED
        policy.cancellation_reason = reason
        policy.end_date = datetime.now()
        
        db.commit()
        db.refresh(policy)
        return policy
