from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

from app.core.database import get_db
from app.models.legal import DocumentType
from app.services.legal_service import LegalService
from app.core.secure_auth import verify_jwt

router = APIRouter(prefix="/legal", tags=["Legal & Configuration"])

@router.get("/config")
async def get_legal_config(db: AsyncSession = Depends(get_db)):
    """
    Fetch public legal configuration (RCCM, DPO email).
    """
    service = LegalService(db)
    config = await service.get_config()
    return {
        "rccm": config.rccm,
        "cc": config.cc,
        "email_dpo": config.email_dpo,
        "artci_authorization": config.artci_authorization
    }

@router.get("/documents/{doc_type}")
async def get_legal_document(
    doc_type: DocumentType,
    user: dict = Depends(verify_jwt),
    db: AsyncSession = Depends(get_db)
):
    """
    Fetch rendered legal text (Privacy Policy, terms of service).
    Must provide a valid JWT to substitute personalized details.
    """
    service = LegalService(db)
    user_data = {
        "user_name": user.get("name", "Cher(e) Client(e)"),
        "user_phone": user.get("phone", "")
    }
    
    try:
        content = await service.render_template(doc_type=doc_type, user_data=user_data)
        return {"doc_type": doc_type, "content": content}
    except Exception as e:
        raise HTTPException(status_code=404, detail="Document not found or error rendering.")
