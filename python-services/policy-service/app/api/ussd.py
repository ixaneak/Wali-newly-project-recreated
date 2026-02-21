from fastapi import APIRouter, Request, Response, Depends
from typing import Optional
import logging
import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.services.ussd.session_manager import USSDSessionManager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ussd", tags=["ussd"])

session_manager = USSDSessionManager()

@router.post("/callback")
async def ussd_callback(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Africa's Talking USSD Gateway Callback
    """
    if "application/json" in request.headers.get("Content-Type", ""):
        data = await request.json()
    else:
        data = dict(await request.form())
        
    session_id = data.get("sessionId")
    phone_number = data.get("phoneNumber")
    text = data.get("text", "")
    
    logger.info(f"USSD session={session_id} phone={phone_number} text={text}")
    
    if not session_id or not phone_number:
        return Response(content="END Erreur technique. Raccrochez et reessayez.", media_type="text/plain")
        
    session = session_manager.get_or_create_session(session_id=session_id, phone=phone_number)
    
    # Process Africa's Talking cumulative text string (e.g. "1*2")
    inputs = text.split('*') if text else []
    last_input = inputs[-1] if inputs else ""
    
    current_state = session.get("state", "welcome")
    
    # Global back/home navigation
    if last_input == "0":
        current_state = session_manager.get_previous_state(session_id)
        last_input = ""
    elif last_input == "00":
        current_state = "welcome"
        session = session_manager.update_state(session_id, current_state)
        last_input = ""
        
    response = ""
    
    # Simplified USSD Menu Logic
    if current_state == "welcome":
        if last_input == "1":
            response = "CON Wali - Souscription\n1. Artisan\n2. Famille\n0. Retour\n00. Accueil"
            session_manager.update_state(session_id, "select_plan")
        elif last_input == "2":
            response = "CON Vos polices actives:\n1. Renouveler\n2. Faire Reclamation\n0. Retour\n00. Accueil"
            session_manager.update_state(session_id, "manage_policies")
        elif last_input == "3":
            response = "CON Entrez votre quartier ou ville pour trouver une pharmacie:\n0. Retour\n00. Accueil"
            session_manager.update_state(session_id, "find_pharmacy")
        else:
            response = "CON Bienvenue sur Wali Assurance\n1. Souscrire\n2. Mes Polices\n3. Trouver Pharmacie"
            
    elif current_state == "select_plan":
        if last_input in ["1", "2"]:
            plan = "artisan" if last_input == "1" else "famille"
            response = f"CON Plan {plan} choisi.\n1. Confirmer (150 CFA/mois)\n2. Annuler\n0. Retour\n00. Accueil"
            session_manager.update_state(session_id, "confirm_subscription", {"selected_plan": plan})
        elif not last_input:
            response = "CON Wali - Souscription\n1. Artisan\n2. Famille\n0. Retour\n00. Accueil"
        else:
            response = "CON Choix invalide.\n1. Artisan\n2. Famille\n0. Retour\n00. Accueil"

    elif current_state == "confirm_subscription":
        if last_input == "1":
            from app.models.policy import Artisan, CoverageSubscription, CoverageType, PolicyStatus
            
            plan = session.get("context", {}).get("selected_plan", "artisan")
            
            # Fetch or create user
            query = select(Artisan).where(Artisan.phone == phone_number)
            result = await db.execute(query)
            artisan = result.scalars().first()

            if not artisan:
                artisan = Artisan(
                    id=uuid.uuid4(),
                    phone=phone_number,
                    first_name="USSD",
                    last_name="User",
                    firebase_uid=f"ussd_{uuid.uuid4().hex[:8]}"
                )
                db.add(artisan)
            
            sub = CoverageSubscription(
                id=uuid.uuid4(),
                artisan_id=artisan.id,
                coverage_type=CoverageType.INDIVIDUAL if plan == "artisan" else CoverageType.FAMILY,
                status=PolicyStatus.PENDING_PAYMENT,
                start_date=datetime.utcnow()
            )
            db.add(sub)
            await db.commit()
            
            response = "END Felicitation! Une demande de paiement Orange Money (150 CFA) a ete envoyee sur votre telephone."
            session_manager.clear_session(session_id)
            
        elif last_input == "2":
            response = "END Souscription annulee."
            session_manager.clear_session(session_id)
        elif not last_input:
            plan = session.get("context", {}).get("selected_plan", "artisan")
            response = f"CON Plan {plan} choisi.\n1. Confirmer (150 CFA/mois)\n2. Annuler\n0. Retour\n00. Accueil"
        else:
            response = "CON Option invalide.\n1. Confirmer\n2. Annuler\n0. Retour"
            
    elif current_state == "manage_policies":
        if last_input == "2":
            from app.models.policy import Artisan
            from app.models.claims import Claim, ClaimType, ClaimStatus
            
            query = select(Artisan).where(Artisan.phone == phone_number)
            result = await db.execute(query)
            artisan = result.scalars().first()
            
            if artisan:
                claim = Claim(
                    id=uuid.uuid4(),
                    artisan_id=artisan.id,
                    claim_type=ClaimType.PHARMACY,
                    amount=0.0,
                    status=ClaimStatus.SUBMITTED
                )
                db.add(claim)
                await db.commit()
                response = f"END Votre demande de reclamation a ete enregistree. Reference: {str(claim.id)[:8]}. Un agent vous contactera."
            else:
                response = "END Vous n'avez pas de profil actif. Veuillez souscrire d'abord."
                
            session_manager.clear_session(session_id)
        elif last_input == "1":
            response = "END Vous n'avez pas de renouvellement en attente."
            session_manager.clear_session(session_id)
        elif not last_input:
            response = "CON Vos polices actives:\n1. Renouveler\n2. Faire Reclamation\n0. Retour\n00. Accueil"
        else:
            response = "CON Choix invalide.\n1. Renouveler\n2. Faire Reclamation\n0. Retour\n00. Accueil"
            
    elif current_state == "find_pharmacy":
        if last_input:
            from app.models.pharmacy import Pharmacy
            query = select(Pharmacy).where(Pharmacy.is_active == True).limit(1)
            result = await db.execute(query)
            pharm = result.scalars().first()
            
            if pharm:
                response = f"END Pharmacie: {pharm.name}\nTel: {pharm.phone}\nAssurance Wali acceptee."
            else:
                response = "END Aucune pharmacie trouvee dans ce secteur."
                
            session_manager.clear_session(session_id)
        else:
            response = "CON Entrez votre quartier ou ville pour trouver une pharmacie:\n0. Retour\n00. Accueil"

    if not response and current_state != "welcome":
        # Global catch-all fallback
        response = "END Session expiree ou erreur technique. Veuillez reessayer."
        session_manager.clear_session(session_id)

    # Return plain text formatted for Africa's Talking USSD protocol
    return Response(content=response, media_type="text/plain")
