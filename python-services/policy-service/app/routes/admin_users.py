from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from app.core.database import get_db
from app.core.security_middleware_v2 import verify_jwt, verify_admin
from app.models.policy import User, KYCStatus, UserRole

router = APIRouter(prefix="/api/v1/users/admin", tags=["admin-users"])

@router.get("", response_model=dict)
def get_admin_users(
    kyc_status: Optional[KYCStatus] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    admin: dict = Depends(verify_admin)
):
    """
    Get all users with filtering and search (admin only).
    """
    query = db.query(User)
    
    if kyc_status:
        query = query.filter(User.kyc_status == kyc_status)
        
    if search:
        # Search by name or phone
        search_filter = f"%{search}%"
        query = query.filter(
            (User.name.ilike(search_filter)) | 
            (User.phone.ilike(search_filter))
        )
        
    total = query.count()
    users = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()
    
    return {
        "items": [u.to_dict() for u in users],
        "total": total,
        "skip": skip,
        "limit": limit
    }

@router.get("/{user_id}", response_model=dict)
def get_user_detail(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: dict = Depends(verify_admin)
):
    """
    Get detailed user profile.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    return user.to_dict()

@router.patch("/{user_id}/kyc", response_model=dict)
def update_user_kyc(
    user_id: uuid.UUID, 
    status: KYCStatus, 
    db: Session = Depends(get_db),
    admin: dict = Depends(verify_admin)
):
    """
    Update user KYC status.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user.kyc_status = status
    db.commit()
    db.refresh(user)
    
    return user.to_dict()
