import unicodedata
from typing import Tuple, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_, inspect

import uuid
from datetime import datetime

from app.models.policy import Artisan, CoverageSubscription, PolicyStatus
from app.models.claims import Claim, ClaimType, ClaimStatus
from app.models.pharmacy import Pharmacy
from app.services.ussd.session_service import USSDSession, USSDSessionService

class USSDFlowEngine:
    """
    USSD Flow Engine handling state transitions and database interactions.
    Strictly enforces 160 character limit per response.
    """
    
    MENUS = {
        "fr": {
            "main_menu": "Wali Assurance\n1. Statut Police\n2. Reclamation\n3. Pharmacie\n4. Langue (Language)",
            "lang_select": "Choisir Langue:\n1. Francais\n2. Dioula\n3. Baoule",
            "not_found": "Dossier introuvable. Souscrivez sur WhatsApp ou appelez le {phone}.",
            "claim_created": "Reclamation {id} ouverte. Envoyez ordonnance sur WhatsApp pour validation.",
            "pharmacy_prompt": "Entrez votre quartier (ex: Cocody, Yopougon):",
            "pharmacy_result": "Pharmacie {name}\nTel:{phone}\nDist: {dist}km",
            "error": "Une erreur est survenue. Tel: {phone}"
        },
        "dy": {
            "main_menu": "Wali Assurance\n1. Police Teliya\n2. Ndimbaya (Reclamation)\n3. Fura-kene (Pharmacie)\n4. Kuma (Langue)",
            "lang_select": "Kuma:\n1. Francais\n2. Dioula\n3. Baoule",
            "not_found": "I ta dosiye tye. I ka souscrire WhatsApp fɛ fɔlɔ. Tel: {phone}",
            "claim_created": "Ndimbaya {id} daminɛna. I ka furu-sɛbɛn blà WhatsApp kàn.",
            "pharmacy_prompt": "I sigiyɔrɔ tɔgɔ sɛbɛn (misa: Abobo):",
            "pharmacy_result": "Fura-kene {name}\nTel:{phone}",
            "error": "Fili dɔ kera. Tel: {phone}"
        },
        "ba": {
            "main_menu": "Wali Assurance\n1. N'zan Police\n2. Mo N'goua (Reclamation)\n3. N'zan Famin (Pharmacie)\n4. Ani (Langue)",
            "lang_select": "Ani:\n1. Francais\n2. Dioula\n3. Baoule",
            "not_found": "E n'zan wla bo. Sran wla WhatsApp le. Tel: {phone}",
            "claim_created": "Mo N'goua {id} b'o. Fa photo kɛ WhatsApp.",
            "pharmacy_prompt": "Amun kulo (ex: Treichville):",
            "pharmacy_result": "N'zan Famin {name}\nTel:{phone}",
            "error": "Nan fɔlɔ. Tel: {phone}"
        }
    }

    def __init__(self, db: AsyncSession, redis_client=None, legal_config=None):
        self.db = db
        self.session_service = USSDSessionService(r=redis_client)
        self.legal_config = legal_config or {}
        self.support_phone = getattr(self.legal_config, 'support_phone', '+225 0101010101') or '+225 0101010101'

    def _get_text(self, lang: str, key: str, **kwargs) -> str:
        text = self.MENUS.get(lang, self.MENUS["fr"]).get(key, self.MENUS["fr"][key])
        if kwargs:
            text = text.format(**kwargs)
        if "{phone}" in text:
            text = text.format(phone=self.support_phone)
        return text[:160] # strictly enforce 160 char limit

    def normalize_location(self, text: str) -> str:
        """Handle accents and typical Ivorian spelling differences."""
        text = text.lower().strip()
        text = ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
        return text

    async def process_input(self, session: USSDSession, user_input: str) -> Tuple[str, bool, USSDSession]:
        """
        Process user input and return (response_text, is_end, updated_session).
        """
        state = session.state
        lang = session.language
        
        if user_input in ["00", "home", "accueil"]:
            session.state = "main_menu"
            session.context = {}
            self.session_service.save_session(session)
            return self._get_text(lang, "main_menu"), False, session

        try:
            if state == "main_menu":
                return await self.handle_main_menu(session, user_input, lang)
            elif state == "view_status":
                return await self._show_policy_status(session, user_input, lang)
            elif state == "file_claim_prompt":
                return await self._handle_claim(session, user_input, lang)
            elif state == "pharmacy_search":
                return await self._handle_pharmacy_search(session, user_input, lang)
            elif state == "select_language":
                return await self.handle_language_select(session, user_input)
            else:
                session.state = "main_menu"
                self.session_service.save_session(session)
                return self._get_text(lang, "main_menu"), False, session
        except Exception as e:
            import logging
            logging.error(f"USSD Flow Error: {e}")
            return self._get_text(lang, "error"), True, session

    async def handle_main_menu(self, session: USSDSession, user_input: str, lang: str):
        if user_input == "1":
            session.state = "view_status"
            self.session_service.save_session(session)
            return await self._show_policy_status(session, "", lang)
        elif user_input == "2":
            session.state = "file_claim_prompt"
            # Proceed directly to attempting to create claim since it's USSD fallback
            return await self._handle_claim(session, "", lang)
        elif user_input == "3":
            session.state = "pharmacy_search"
            self.session_service.save_session(session)
            return self._get_text(lang, "pharmacy_prompt"), False, session
        elif user_input == "4":
            session.state = "select_language"
            self.session_service.save_session(session)
            return self._get_text(lang, "lang_select"), False, session
        else:
            return self._get_text(lang, "main_menu"), False, session

    async def handle_language_select(self, session: USSDSession, user_input: str):
        if user_input == "1":
            session.language = "fr"
        elif user_input == "2":
            session.language = "dy"
        elif user_input == "3":
            session.language = "ba"
            
        session.state = "main_menu"
        self.session_service.save_session(session)
        return self._get_text(session.language, "main_menu"), False, session

    async def _show_policy_status(self, session: USSDSession, user_input: str, lang: str):
        # Query PostgreSQL
        query = select(Artisan, CoverageSubscription).join(
            CoverageSubscription, Artisan.id == CoverageSubscription.artisan_id
        ).where(Artisan.phone == session.phone_number).limit(1)
        
        result = await self.db.execute(query)
        row = result.first()
        
        if not row:
            session.state = "main_menu"
            self.session_service.save_session(session)
            return self._get_text(lang, "not_found"), True, session
            
        artisan, sub = row
        status_fr = "Active" if sub.status == PolicyStatus.ACTIVE else "En Attente"
        
        text = f"{artisan.first_name}, Statut: {status_fr}\nExp: {sub.end_date.strftime('%d/%m/%Y') if sub.end_date else 'N/A'}"
        return text[:160], True, session

    async def _handle_claim(self, session: USSDSession, user_input: str, lang: str):
        # Find artisan
        query = select(Artisan).where(Artisan.phone == session.phone_number)
        result = await self.db.execute(query)
        artisan = result.scalars().first()
        
        if not artisan:
            return self._get_text(lang, "not_found"), True, session

        # Create Claim
        claim_id = uuid.uuid4()
        claim = Claim(
            id=claim_id,
            artisan_id=artisan.id,
            claim_type=ClaimType.PHARMACY,
            amount=0.0,
            status=ClaimStatus.PENDING_DOCUMENTS # Awaiting WhatsApp photos
        )
        self.db.add(claim)
        await self.db.commit()
        
        short_id = str(claim_id)[:6].upper()
        return self._get_text(lang, "claim_created", id=short_id), True, session

    async def _handle_pharmacy_search(self, session: USSDSession, user_input: str, lang: str):
        if not user_input:
            return self._get_text(lang, "pharmacy_prompt"), False, session
            
        loc = self.normalize_location(user_input)
        
        # Fuzzy search Pharmacy table
        query = select(Pharmacy).where(
            Pharmacy.is_active == True,
            or_(
                Pharmacy.name.ilike(f"%{loc}%"),
                Pharmacy.address.ilike(f"%{loc}%")
            )
        ).limit(1)
        
        result = await self.db.execute(query)
        pharmacy = result.scalars().first()
        
        if pharmacy:
            return self._get_text(lang, "pharmacy_result", name=pharmacy.name[:20], phone=pharmacy.phone, dist="N/A"), True, session
            
        return "Aucune pharmacie trouvee dans ce secteur.", True, session
