from fastapi import APIRouter, Request, Response, Depends, HTTPException
import logging
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.config import get_settings
from app.services.ussd.africas_talking import AfricasTalkingProvider
from app.services.ussd.session_service import USSDSessionService
from app.services.ussd.flow_engine import USSDFlowEngine
from app.models.ussd import USSDSessionLog

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ussd", tags=["ussd"])
settings = get_settings()

at_provider = AfricasTalkingProvider(
    api_key=getattr(settings, "at_api_key", ""),
    username=getattr(settings, "at_username", "")
)

@router.get("/health")
async def ussd_health():
    """Health check for USSD endpoint."""
    return {"status": "ok", "service": "ussd"}

@router.post("/callback")
async def ussd_callback(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Africa's Talking USSD Gateway Callback.
    Integrated with Flow Engine and Redis Session Service.
    """
    if "application/json" in request.headers.get("Content-Type", ""):
        data = await request.json()
    else:
        data = dict(await request.form())
        
    parsed = at_provider.parse_request(data)
    session_id = parsed["session_id"]
    phone_number = parsed["phone_number"]
    network_code = parsed["network_code"]
    text = parsed["text"]
    
    logger.info(f"USSD session={session_id} phone={phone_number} text={text}")
    
    if not session_id or not phone_number:
        return Response(
            content=at_provider.format_response("Erreur technique. Raccrochez et reessayez.", is_end=True),
            media_type="text/plain"
        )
        
    # Security: Verify Signature (if AT implements signature in headers, we'd check it here)
    # signature = request.headers.get('AT-Signature') 
    # if signature and not at_provider.verify_callback(await request.body(), signature):
    #    return Response(content="END Invalid Signature", media_type="text/plain", status_code=403)
        
    from app.services.legal_service import LegalService
    legal_service = LegalService(db)
    legal_config = await legal_service.get_config()
    
    engine = USSDFlowEngine(db=db, legal_config=legal_config)
    session_service = engine.session_service
    
    session = session_service.get_or_create_session(session_id=session_id, phone=phone_number)
    
    # Process Africa's Talking cumulative text string (e.g. "1*2")
    inputs = text.split('*') if text else []
    last_input = inputs[-1] if inputs else ""
    
    # Process through Flow Engine
    response_text, is_end, updated_session = await engine.process_input(session, last_input)
    
    # Log Session if ended
    if is_end:
        try:
            log_entry = USSDSessionLog(
                session_id=session_id,
                phone_number=phone_number,
                network_code=network_code,
                screens_visited=len(inputs) + 1,
                final_state=updated_session.state,
                ended_at=datetime.utcnow()
            )
            db.add(log_entry)
            await db.commit()
        except Exception as e:
            logger.error(f"Failed to log USSD session: {e}")
            await db.rollback()

    formatted_response = at_provider.format_response(response_text, is_end=is_end)
    return Response(content=formatted_response, media_type="text/plain")
