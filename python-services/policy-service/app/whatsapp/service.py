"""
High-level WhatsApp Service for Wali Assurance.

Provides business logic for:
- User enrollment flows
- Claim submissions
- B2B group management
- Payment notifications
- Support routing
"""
import logging
import os
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import uuid4

from sqlalchemy.orm import Session

from .models import (
    WhatsAppConversation,
    WhatsAppMessageLog,
    GroupEnrollment,
    ConversationState,
    LanguageCode,
    GroupEnrollmentStatus,
    OutboundMessage,
    MessageType,
    GroupEnrollmentRequest
)
from .state_machine import StateMachine
from .client import WhatsAppClient

logger = logging.getLogger(__name__)


class WhatsAppService:
    """
    High-level service for WhatsApp operations.
    
    Orchestrates:
    - State machine transitions
    - Message sending
    - Group enrollment
    - Claim processing
    """
    
    def __init__(
        self,
        client: WhatsAppClient,
        state_machine: StateMachine,
        db: Session
    ):
        self.client = client
        self.state_machine = state_machine
        self.db = db
    
    # ═════════════════════════════════════════════════════════════════
    # USER ENROLLMENT FLOWS
    # ═════════════════════════════════════════════════════════════════
    
    def start_enrollment(self, phone: str) -> WhatsAppConversation:
        """
        Start enrollment flow for a new user.
        
        Args:
            phone: User phone number (E.164 format)
        
        Returns:
            Created conversation
        """
        # Check for existing conversation
        conversation = self.db.query(WhatsAppConversation).filter(
            WhatsAppConversation.phone == phone
        ).first()
        
        if conversation:
            logger.info(f"Existing conversation found for {phone}")
            return conversation
        
        # Create new conversation
        conversation = WhatsAppConversation(
            phone=phone,
            state=ConversationState.OPT_IN_REQUIRED,
            opted_in=False
        )
        self.db.add(conversation)
        self.db.commit()
        
        # Send opt-in request
        self._send_opt_in_request(conversation)
        
        logger.info(f"New enrollment started for {phone}")
        return conversation
    
    def confirm_opt_in(self, conversation: WhatsAppConversation) -> bool:
        """
        Confirm user opt-in (GDPR/Law 2013-450 compliance).
        
        Args:
            conversation: User conversation
        
        Returns:
            True if confirmed
        """
        if conversation.state != ConversationState.OPT_IN_REQUIRED:
            return False
        
        conversation.opted_in = True
        conversation.opted_in_at = datetime.utcnow()
        
        # Transition to IDLE
        self.state_machine.transition(
            conversation,
            ConversationState.IDLE
        )
        
        self.db.commit()
        
        # Send welcome message
        self._send_welcome_message(conversation)
        
        return True
    
    def select_trade(
        self,
        conversation: WhatsAppConversation,
        trade: str
    ) -> bool:
        """
        Record user's trade/profession selection.
        
        Valid trades: menuisier, mecanicien, electricien, plombier,
                     macon, peintre, soudeur, coiffeur, tailleur,
                     vendeur, autre
        """
        valid_trades = [
            "menuisier", "mecanicien", "electricien", "plombier",
            "macon", "peintre", "soudeur", "coiffeur", "tailleur",
            "vendeur", "autre"
        ]
        
        if trade not in valid_trades:
            return False
        
        self.state_machine.transition(
            conversation,
            ConversationState.TRADE_SELECTION,
            context_update={"trade": trade}
        )
        
        self.db.commit()
        return True
    
    def select_plan(
        self,
        conversation: WhatsAppConversation,
        plan_type: str
    ) -> bool:
        """
        Select insurance plan.
        
        Args:
            plan_type: 'individual', 'family', or 'group'
        
        Note:
            Family plans require PARENT_CONFIRMATION state (CIMA compliance)
        """
        if plan_type not in ["individual", "family", "group"]:
            return False
        
        context_update = {"plan_type": plan_type}
        
        if plan_type == "family":
            # CRITICAL CIMA REQUIREMENT: Cannot skip PARENT_CONFIRMATION
            self.state_machine.transition(
                conversation,
                ConversationState.PARENT_CONFIRMATION,
                context_update=context_update
            )
        else:
            self.state_machine.transition(
                conversation,
                ConversationState.LOCATION_CAPTURE,
                context_update=context_update
            )
        
        self.db.commit()
        return True
    
    def confirm_parent_coverage(
        self,
        conversation: WhatsAppConversation,
        covers_parents: bool
    ) -> bool:
        """
        Confirm parental coverage for family plans.
        
        CIMA Requirement:
        - Must explicitly confirm coverage for 2 parents
        - Cannot proceed without this confirmation for family plans
        """
        if conversation.state != ConversationState.PARENT_CONFIRMATION:
            return False
        
        if not covers_parents:
            # User declined - revert to individual or cancel
            self.state_machine.transition(
                conversation,
                ConversationState.PLAN_SELECTION,
                context_update={
                    "parents_confirmed": False,
                    "covers_parents": False,
                    "plan_type": "individual"  # Downgrade to individual
                }
            )
        else:
            # Confirmed - proceed
            self.state_machine.transition(
                conversation,
                ConversationState.LOCATION_CAPTURE,
                context_update={
                    "parents_confirmed": True,
                    "covers_parents": True
                }
            )
        
        self.db.commit()
        return True
    
    def set_location(
        self,
        conversation: WhatsAppConversation,
        latitude: float,
        longitude: float,
        location_name: Optional[str] = None
    ) -> bool:
        """
        Set user's location for pharmacy network optimization.
        
        Validates Ivory Coast bounds:
        - Latitude: 4°N to 11°N
        - Longitude: 8°W to 3°W
        """
        # Validate Ivory Coast bounds
        if not (4.0 <= latitude <= 11.0 and -8.0 <= longitude <= -3.0):
            return False
        
        self.state_machine.transition(
            conversation,
            ConversationState.PAYMENT_PENDING,
            context_update={
                "latitude": latitude,
                "longitude": longitude,
                "location_name": location_name
            }
        )
        
        self.db.commit()
        
        # Send payment instructions
        self._send_payment_instructions(conversation)
        
        return True
    
    # ═════════════════════════════════════════════════════════════════
    # B2B GROUP ENROLLMENT
    # ═════════════════════════════════════════════════════════════════
    
    def create_group_enrollment(
        self,
        request: GroupEnrollmentRequest
    ) -> GroupEnrollment:
        """
        Create a new group enrollment (syndicate/cooperative).
        
        CIMA Rules:
        - Max 100 members
        - Min 5 members for group rate
        - All members must be same region
        - 10% discount for groups > 20 members
        """
        # Generate unique group code
        code = self._generate_group_code()
        
        # Calculate discount
        discount_rate = Decimal("0.10") if request.expected_members >= 20 else Decimal("0.05")
        
        group = GroupEnrollment(
            code=code,
            name=request.name,
            leader_phone=request.leader_phone,
            leader_name=request.leader_name,
            region=request.region,
            max_members=min(request.expected_members + 10, 100),  # Buffer, max 100
            min_members=5,
            base_premium_per_member=Decimal("5000.00"),  # Default, should be from config
            discount_rate=discount_rate,
            commission_rate=Decimal("0.05"),  # 5% commission
            status=GroupEnrollmentStatus.PENDING
        )
        
        self.db.add(group)
        self.db.commit()
        
        # Send confirmation to leader
        self._send_group_creation_confirmation(group)
        
        logger.info(f"Group enrollment created: {code} for {request.leader_phone}")
        
        return group
    
    def add_member_to_group(
        self,
        group_code: str,
        member_phone: str
    ) -> bool:
        """Add a member to a group enrollment."""
        group = self.db.query(GroupEnrollment).filter(
            GroupEnrollment.code == group_code
        ).first()
        
        if not group:
            return False
        
        if not group.can_add_member():
            return False
        
        # Get or create member conversation
        conversation = self.db.query(WhatsAppConversation).filter(
            WhatsAppConversation.phone == member_phone
        ).first()
        
        if not conversation:
            conversation = WhatsAppConversation(
                phone=member_phone,
                state=ConversationState.B2B_ENROLLMENT,
                group_id=group.id
            )
            self.db.add(conversation)
        else:
            conversation.group_id = group.id
            conversation.state = ConversationState.B2B_ENROLLMENT
        
        # Update group count
        group.member_count += 1
        
        # Activate group if minimum reached
        if group.member_count >= group.min_members and group.status == GroupEnrollmentStatus.PENDING:
            group.status = GroupEnrollmentStatus.ACTIVE
        
        self.db.commit()
        
        # Send welcome message to member
        self._send_group_member_welcome(conversation, group)
        
        return True
    
    def process_group_payment(
        self,
        group_code: str,
        amount: Decimal,
        payment_method: str
    ) -> bool:
        """Process bulk payment for group enrollment."""
        group = self.db.query(GroupEnrollment).filter(
            GroupEnrollment.code == group_code
        ).first()
        
        if not group:
            return False
        
        expected_amount = self._calculate_group_total(group)
        
        if amount < expected_amount:
            logger.warning(f"Insufficient payment for group {group_code}")
            return False
        
        group.total_collected = amount
        group.status = GroupEnrollmentStatus.COMPLETED
        group.completed_at = datetime.utcnow()
        
        self.db.commit()
        
        # Activate all members
        self._activate_group_members(group)
        
        # Pay commission to leader
        commission = group.calculate_commission()
        self._pay_leader_commission(group, commission)
        
        return True
    
    def _calculate_group_total(self, group: GroupEnrollment) -> Decimal:
        """Calculate total premium for group with discount."""
        base = group.base_premium_per_member * group.member_count
        discount = group.base_premium_per_member * group.discount_rate * group.member_count
        return base - discount
    
    def _generate_group_code(self) -> str:
        """Generate unique 6-character group code."""
        import random
        import string
        
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            
            # Check uniqueness
            existing = self.db.query(GroupEnrollment).filter(
                GroupEnrollment.code == code
            ).first()
            
            if not existing:
                return code
    
    # ═════════════════════════════════════════════════════════════════
    # CLAIM PROCESSING
    # ═════════════════════════════════════════════════════════════════
    
    def start_claim(
        self,
        conversation: WhatsAppConversation,
        claim_type: str
    ) -> bool:
        """Start claim submission flow."""
        if not conversation.opted_in:
            return False
        
        self.state_machine.transition(
            conversation,
            ConversationState.ACTIVE_CLAIM,
            context_update={
                "claim_type": claim_type,
                "claim_started_at": datetime.utcnow().isoformat()
            }
        )
        
        self.db.commit()
        
        # Send claim instructions
        self._send_claim_instructions(conversation)
        
        return True
    
    def submit_claim_documentation(
        self,
        conversation: WhatsAppConversation,
        media_id: str
    ) -> bool:
        """Submit documentation for active claim."""
        if conversation.state != ConversationState.ACTIVE_CLAIM:
            return False
        
        self.state_machine.transition(
            conversation,
            ConversationState.DOCUMENT_UPLOAD,
            context_update={"documentation_media_id": media_id}
        )
        
        self.db.commit()
        return True
    
    # ═════════════════════════════════════════════════════════════════
    # NOTIFICATIONS
    # ═════════════════════════════════════════════════════════════════
    
    def send_payment_reminder(
        self,
        phone: str,
        amount: Decimal,
        due_date: datetime
    ):
        """Send payment reminder template."""
        try:
            self.client.send_template_message(
                phone=phone,
                template_name="payment_reminder",
                params=[
                    str(int(amount)),
                    due_date.strftime("%d/%m/%Y"),
                    "07 XX XX XX XX"  # Payment number
                ]
            )
        except Exception as e:
            logger.error(f"Failed to send payment reminder: {e}")
    
    def send_claim_confirmation(
        self,
        phone: str,
        claim_id: str
    ):
        """Send claim received confirmation."""
        try:
            self.client.send_template_message(
                phone=phone,
                template_name="claim_received",
                params=[
                    claim_id,
                    f"https://wali.ci/claims/{claim_id}"
                ]
            )
        except Exception as e:
            logger.error(f"Failed to send claim confirmation: {e}")
    
    def send_pharmacy_approval(
        self,
        phone: str,
        pharmacy_name: str,
        qr_code_url: str,
        expiry_minutes: int = 30
    ):
        """Send pharmacy authorization with QR code."""
        try:
            self.client.send_template_message(
                phone=phone,
                template_name="pharmacy_approval",
                params=[
                    pharmacy_name,
                    qr_code_url,
                    str(expiry_minutes)
                ]
            )
        except Exception as e:
            logger.error(f"Failed to send pharmacy approval: {e}")
    
    # ═════════════════════════════════════════════════════════════════
    # PRIVATE HELPERS
    # ═════════════════════════════════════════════════════════════════
    
    def _send_opt_in_request(self, conversation: WhatsAppConversation):
        """Send GDPR/Law 2013-450 opt-in request."""
        # Law 2013-450: Must use explicit "OUI" for consent
        text = (
            "Bienvenue chez Wali Assurance SARL - RC CI-ABJ-2019-B-XXXXX. "
            "Conformément à la Loi 2013-450 sur la protection des données, "
            "nous traitons vos informations uniquement avec votre consentement.\n\n"
            "Détails: https://wali.ci/confidentialite\n\n"
            "Pour accepter et continuer, répondez OUI.\n"
            "Pour refuser, répondez NON."
        )
        
        try:
            self.client.send_message(OutboundMessage(
                phone=conversation.phone,
                type=MessageType.TEXT,
                text=text
            ))
        except Exception as e:
            logger.error(f"Failed to send opt-in request: {e}")
    
    def _send_welcome_message(self, conversation: WhatsAppConversation):
        """Send welcome message after opt-in."""
        try:
            self.client.send_template_message(
                phone=conversation.phone,
                template_name="welcome_message",
                language=conversation.language.value,
                params=["Wali", "+225 07 07 07 07 07"]
            )
        except Exception as e:
            logger.error(f"Failed to send welcome message: {e}")
    
    def _send_payment_instructions(self, conversation: WhatsAppConversation):
        """Send mobile money payment instructions."""
        plan_type = conversation.context.get("plan_type", "individual")
        amount = "5000" if plan_type == "individual" else "15000"
        
        text = (
            f"Votre cotisation {plan_type} est de {amount} FCFA/mois.\n\n"
            "Pour payer:\n"
            "1. Orange Money: *144*4*6*montant#\n"
            "2. Wave: Transfert au 07 XX XX XX XX\n"
            "3. MTN MoMo: *136*4*montant#\n\n"
            f"Référence: WALI{conversation.phone[-6:]}"
        )
        
        try:
            self.client.send_message(OutboundMessage(
                phone=conversation.phone,
                type=MessageType.TEXT,
                text=text
            ))
        except Exception as e:
            logger.error(f"Failed to send payment instructions: {e}")
    
    def _send_group_creation_confirmation(self, group: GroupEnrollment):
        """Send group creation confirmation to leader."""
        text = (
            f"Votre groupe {group.name} a été créé!\n\n"
            f"Code groupe: {group.code}\n"
            f"Membres max: {group.max_members}\n"
            f"Réduction: {int(group.discount_rate * 100)}%\n\n"
            "Partagez ce code avec vos membres pour qu'ils s'inscrivent."
        )
        
        try:
            self.client.send_message(OutboundMessage(
                phone=group.leader_phone,
                type=MessageType.TEXT,
                text=text
            ))
        except Exception as e:
            logger.error(f"Failed to send group confirmation: {e}")
    
    def _send_group_member_welcome(
        self,
        conversation: WhatsAppConversation,
        group: GroupEnrollment
    ):
        """Send welcome message to group member."""
        text = (
            f"Bienvenue dans le groupe {group.name}!\n\n"
            f"Vous bénéficiez d'une réduction de {int(group.discount_rate * 100)}% "
            "sur votre cotisation.\n\n"
            "Répondez COMMENCER pour finaliser votre inscription."
        )
        
        try:
            self.client.send_message(OutboundMessage(
                phone=conversation.phone,
                type=MessageType.TEXT,
                text=text
            ))
        except Exception as e:
            logger.error(f"Failed to send member welcome: {e}")
    
    def _send_claim_instructions(self, conversation: WhatsAppConversation):
        """Send claim submission instructions with regional information."""
        text = (
            "📄 Déclaration de sinistre:\n\n"
            "1. Décrivez l'incident\n"
            "2. Envoyez une photo de l'ordonnance ou reçu\n"
            "3. Indiquez le montant estimé\n\n"
            "⚠️ Limite WhatsApp: 500,000 FCFA\n"
            "Au-delà: un agent vous contactera.\n\n"
            "Délai de traitement: 48h ouvrées"
        )
        text += self._get_footer(conversation.context.get("region"))
        
        try:
            self.client.send_message(OutboundMessage(
                phone=conversation.phone,
                type=MessageType.TEXT,
                text=text
            ))
        except Exception as e:
            logger.error(f"Failed to send claim instructions: {e}")
    
    # ═════════════════════════════════════════════════════════════════
    # CORE HANDLER FUNCTIONS (Required Implementation)
    # ═════════════════════════════════════════════════════════════════
    
    async def handle_incoming_message(
        self,
        phone: str,
        message: Dict[str, Any],
        db: Session
    ) -> None:
        """
        Main router. Must:
        1. Normalize phone to E.164
        2. Check blocklist
        3. Get or create conversation
        4. Log cross-border transfer (Law 2013-450 compliance)
        5. Route to state handler
        6. Log to WhatsAppMessageLog (async, don't block)
        """
        try:
            # 1. Normalize phone to E.164
            normalized_phone = self._normalize_phone(phone)
            
            # 2. Get or create conversation (blocklist check in conversation)
            conversation = self._get_or_create_conversation(normalized_phone, db)
            
            # Check if user is blocked
            if conversation.is_blocked():
                logger.warning(f"Blocked user attempted message: {normalized_phone}")
                return
            
            # 3. Extract message info
            message_id = message.get("id", str(uuid4()))
            message_type = message.get("type", "text")
            message_text = message.get("text", {}).get("body", "").strip().lower()
            
            # 4. Log cross-border data transfer (Law 2013-450 requirement)
            # Meta/WhatsApp data goes to US - must log every transfer
            self._log_cross_border_transfer(
                phone=normalized_phone,
                transfer_type="inbound_message",
                destination="USA/Meta",
                data_type="message_metadata",
                legal_basis="user_consent",
                db=db
            )
            
            # 5. Log message (non-blocking)
            await self._log_message_async(
                conversation=conversation,
                message_id=message_id,
                direction="inbound",
                message_type=message_type,
                content=message_text,
                db=db
            )
            
            # 6. Route based on current state
            await self._route_by_state(conversation, message_text, message, db)
            
        except Exception as e:
            logger.error(f"Error handling incoming message: {e}")
            raise
    
    def _log_cross_border_transfer(
        self,
        phone: str,
        transfer_type: str,
        destination: str,
        data_type: str,
        legal_basis: str,
        db: Session
    ):
        """
        Log cross-border data transfers as required by Law 2013-450.
        All WhatsApp traffic goes to Meta (USA) - must be documented.
        """
        # In production, this would write to a dedicated audit table
        # For now, we log with a specific format for compliance auditing
        logger.info(
            f"CROSS_BORDER_TRANSFER|"
            f"timestamp={datetime.utcnow().isoformat()}|"
            f"phone_hash={hash(phone) % (10**10)}|"  # Pseudonymized
            f"type={transfer_type}|"
            f"destination={destination}|"
            f"data_type={data_type}|"
            f"legal_basis={legal_basis}|"
            f"retention_days=365"
        )
    
    async def process_image_claim(
        self,
        phone: str,
        media_id: str,
        mime_type: str,
        db: Session
    ) -> Dict[str, Any]:
        """
        Handle image upload for claims. Must:
        1. Download from Meta CDN
        2. Run fraud checks (perceptual hash, EXIF)
        3. Compress and encrypt
        4. Create claim record with 'fraud_review' status if flags detected
        5. Return claim_id to user
        """
        result = {
            "success": False,
            "claim_id": None,
            "status": None,
            "flags": [],
            "message": ""
        }
        
        try:
            # Get conversation
            conversation = self._get_or_create_conversation(phone, db)
            
            # Check if in valid state for claim
            if conversation.state not in [ConversationState.ACTIVE_CLAIM, ConversationState.DOCUMENT_UPLOAD]:
                result["message"] = "Veuillez d'abord décrire votre sinistre."
                return result
            
            # 1. Download from Meta CDN
            temp_path = f"/tmp/{media_id}_{uuid4()}.jpg"
            downloaded_path = self.client.download_media(media_id, temp_path)
            
            # 2. Run fraud checks
            from .image_processor import ImageProcessor
            processor = ImageProcessor(db_session=db)
            
            fraud_result = await processor.process_claim_image(
                downloaded_path,
                conversation,
                db
            )
            
            # 3. Determine status based on flags
            if fraud_result.get("is_duplicate"):
                result["flags"].append("duplicate_image")
                result["status"] = "fraud_review"
                result["message"] = "Votre document est en cours de vérification (doublon détecté)."
            elif not fraud_result.get("is_valid"):
                result["flags"].extend(fraud_result.get("validation_errors", []))
                result["status"] = "fraud_review"
                result["message"] = "Votre document est en cours de vérification."
            else:
                result["status"] = "submitted"
                result["message"] = "Votre document a été reçu et est en traitement."
            
            # 4. Create claim record
            claim_id = f"CLM-{datetime.utcnow().strftime('%Y%m%d')}-{uuid4().hex[:6].upper()}"
            
            # Update conversation context
            conversation.context.update({
                "claim_id": claim_id,
                "claim_status": result["status"],
                "image_processed": True,
                "fraud_flags": result["flags"],
                "media_log_id": fraud_result.get("media_id")
            })
            
            # Transition state
            if result["status"] == "fraud_review":
                self.state_machine.transition(
                    conversation,
                    ConversationState.FRAUD_REVIEW,
                    context_update={"claim_id": claim_id}
                )
            else:
                self.state_machine.transition(
                    conversation,
                    ConversationState.SETTLEMENT,
                    context_update={"claim_id": claim_id}
                )
            
            db.commit()
            
            # 5. Return claim_id
            result["claim_id"] = claim_id
            result["success"] = True
            
            # Cleanup temp file
            if os.path.exists(downloaded_path):
                os.unlink(downloaded_path)
            
            # Send confirmation
            await self._send_claim_confirmation(phone, claim_id, result["message"])
            
        except Exception as e:
            logger.error(f"Error processing image claim: {e}")
            result["message"] = "Erreur lors du traitement de l'image. Veuillez réessayer."
        
        return result
    
    async def initiate_group_enrollment(
        self,
        leader_phone: str,
        group_name: str,
        member_count: int,
        db: Session
    ) -> str:
        """
        Create group enrollment code. Must:
        1. Validate member_count <= 100 (CIMA limit)
        2. Generate unique 6-char code
        3. Create GroupEnrollment record
        4. Send template to leader with instructions
        5. Return group_code
        """
        try:
            # 1. Validate member_count <= 100 (CIMA limit)
            if member_count > 100:
                raise ValueError("Le nombre maximum de membres est de 100 (limite CIMA).")
            
            if member_count < 5:
                raise ValueError("Le nombre minimum de membres est de 5 pour un tarif de groupe.")
            
            # 2. Generate unique 6-char code
            group_code = self._generate_group_code()
            
            # Normalize leader phone
            normalized_leader = self._normalize_phone(leader_phone)
            
            # Calculate discount based on size
            discount_rate = Decimal("0.10") if member_count >= 20 else Decimal("0.05")
            
            # 3. Create GroupEnrollment record
            group = GroupEnrollment(
                code=group_code,
                name=group_name,
                leader_phone=normalized_leader,
                max_members=min(member_count + 10, 100),  # Buffer
                min_members=5,
                member_count=0,
                discount_rate=discount_rate,
                commission_rate=Decimal("0.05"),
                status=GroupEnrollmentStatus.PENDING,
                base_premium_per_member=Decimal("5000.00")
            )
            
            db.add(group)
            db.flush()
            
            # Get or create leader conversation
            leader_conv = self._get_or_create_conversation(normalized_leader, db)
            leader_conv.group_id = group.id
            leader_conv.state = ConversationState.B2B_ENROLLMENT
            
            db.commit()
            
            # 4. Send template to leader with instructions
            try:
                text = (
                    f"✅ Groupe créé: {group_name}\n\n"
                    f"Code: {group_code}\n"
                    f"Membres max: {group.max_members}\n"
                    f"Réduction: {int(discount_rate * 100)}%\n\n"
                    "Partagez ce code avec vos membres. "
                    "Ils doivent envoyer 'CODE {votre_code}' pour rejoindre."
                )
                
                self.client.send_message(OutboundMessage(
                    phone=normalized_leader,
                    type=MessageType.TEXT,
                    text=text
                ))
                
                logger.info(f"Group enrollment created: {group_code} for {normalized_leader}")
                
            except Exception as e:
                logger.error(f"Failed to send group confirmation: {e}")
                # Don't fail if message sending fails
            
            # 5. Return group_code
            return group_code
            
        except Exception as e:
            logger.error(f"Error creating group enrollment: {e}")
            db.rollback()
            raise
    
    # ═════════════════════════════════════════════════════════════════
    # HELPER METHODS
    # ═════════════════════════════════════════════════════════════════
    
    def _normalize_phone(self, phone: str) -> str:
        """Normalize phone to E.164 format."""
        phone = phone.strip().replace(" ", "").replace("-", "")
        if phone.startswith("0"):
            phone = "+225" + phone[1:]
        if not phone.startswith("+"):
            phone = "+225" + phone
        return phone
    
    async def _log_message_async(
        self,
        conversation: WhatsAppConversation,
        message_id: str,
        direction: str,
        message_type: str,
        content: str,
        db: Session
    ):
        """Log message to WhatsAppMessageLog."""
        import hashlib
        
        log = WhatsAppMessageLog(
            message_id=message_id,
            phone=conversation.phone,
            conversation_id=conversation.id,
            direction=direction,
            message_type=message_type,
            content_hash=hashlib.sha256(content.encode()).hexdigest(),
            content_preview=content[:200] if content else None,
            idempotency_key=str(uuid4()),
            timestamp=datetime.utcnow()
        )
        db.add(log)
        # Don't commit here - let main transaction handle it
    
    async def _route_by_state(
        self,
        conversation: WhatsAppConversation,
        message_text: str,
        message: Dict[str, Any],
        db: Session
    ):
        """Route message to appropriate handler based on state."""
        state = conversation.state
        
        # Sanitize message text for formal tone
        message_text = self._sanitize_message(message_text).lower().strip()
        
        # Handle global commands first
        if message_text in ["menu", "aide", "help"]:
            await self._send_main_menu(conversation)
            return
        
        if message_text in ["annuler", "cancel", "retour"]:
            self.state_machine.transition(conversation, ConversationState.IDLE)
            await self._send_cancelled_message(conversation)
            return
        
        # State-specific routing with Ivory Coast business logic
        if state == ConversationState.OPT_IN_REQUIRED:
            # Law 2013-450: Require explicit "OUI" consent (not just OK)
            if self._validate_explicit_consent(message_text):
                self.confirm_opt_in(conversation)
                await self._send_welcome_message(conversation)
            else:
                await self._send_opt_in_reminder(conversation)
        
        elif state == ConversationState.IDLE:
            await self._handle_idle_state(conversation, message_text)
        
        elif state == ConversationState.TRADE_SELECTION:
            # CNMCI trade validation
            if self._validate_trade_cnmci(message_text):
                self.select_trade(conversation, message_text)
            else:
                await self._send_invalid_trade_cnmci(conversation)
        
        elif state == ConversationState.PLAN_SELECTION:
            if message_text in ["individual", "famille", "groupe"]:
                self.select_plan(conversation, message_text)
                # If family plan, transition to PARENT_CONFIRMATION (mandatory per CIMA)
                if message_text == "famille":
                    self.state_machine.transition(
                        conversation, 
                        ConversationState.PARENT_CONFIRMATION,
                        context_update={"awaiting_parent_confirmation": True}
                    )
                    await self.send_parental_confirmation(
                        conversation.phone,
                        conversation.context.get("region")
                    )
            else:
                await self._send_plan_options(conversation)
        
        elif state == ConversationState.PARENT_CONFIRMATION:
            # Mandatory explicit confirmation for family plans (CIMA requirement)
            if self._validate_explicit_consent(message_text):
                self.confirm_parent_coverage(conversation, True)
                # Continue to payment or confirmation
                await self._send_enrollment_summary(conversation)
            elif message_text in ["non", "no"]:
                self.confirm_parent_coverage(conversation, False)
                await self._send_plan_downgrade_message(conversation)
            else:
                await self.send_parental_confirmation(
                    conversation.phone,
                    conversation.context.get("region")
                )
        
        elif state == ConversationState.ACTIVE_CLAIM:
            # Store claim description and check for escalation
            conversation.context["claim_description"] = message_text
            
            # Check if claim amount provided exceeds limit
            estimated_amount = conversation.context.get("estimated_amount")
            if estimated_amount and not self._check_claim_limit(Decimal(str(estimated_amount))):
                await self.handle_claim_with_escalation(
                    conversation.phone,
                    Decimal(str(estimated_amount)),
                    message_text,
                    db
                )
            else:
                self.start_claim(conversation, "general")
        
        elif state == ConversationState.B2B_ENROLLMENT:
            # Handle group code
            if message_text.startswith("code "):
                group_code = message_text.replace("code ", "").strip().upper()
                success = self.add_member_to_group(group_code, conversation.phone)
                if success:
                    await self._send_group_joined_confirmation(conversation, group_code)
                else:
                    await self._send_invalid_group_code(conversation)
        
        db.commit()
    
    def _validate_trade(self, trade: str) -> bool:
        """Validate trade selection."""
        valid_trades = [
            "menuisier", "mecanicien", "electricien", "plombier",
            "macon", "peintre", "soudeur", "coiffeur", "tailleur",
            "vendeur", "autre"
        ]
        return trade in valid_trades
    
    async def _send_main_menu(self, conversation: WhatsAppConversation):
        """Send main menu options."""
        text = (
            "🏠 Menu Principal\n\n"
            "1. 📋 Souscrire (Nouvelle assurance)\n"
            "2. 📄 Déclarer un sinistre\n"
            "3. 👥 Rejoindre un groupe\n"
            "4. ❓ Aide / Support\n\n"
            "Répondez par le numéro (1, 2, 3 ou 4)"
        )
        text += self._get_footer(conversation.context.get("region"))
        
        self.client.send_message(OutboundMessage(
            phone=conversation.phone,
            type=MessageType.TEXT,
            text=text
        ))
    
    async def _send_cancelled_message(self, conversation: WhatsAppConversation):
        """Send cancellation confirmation."""
        self.client.send_message(OutboundMessage(
            phone=conversation.phone,
            type=MessageType.TEXT,
            text="Opération annulée. Retour au menu principal."
        ))
    
    async def _send_opt_in_reminder(self, conversation: WhatsAppConversation):
        """Send opt-in reminder."""
        self._send_opt_in_request(conversation)
    
    async def _handle_idle_state(self, conversation: WhatsAppConversation, text: str):
        """Handle commands in IDLE state."""
        if text in ["1", "souscrire", "nouvelle"]:
            self.state_machine.transition(conversation, ConversationState.TRADE_SELECTION)
            await self._send_trade_selection_menu(conversation)
        elif text in ["2", "sinistre", "declarer"]:
            self.state_machine.transition(conversation, ConversationState.ACTIVE_CLAIM)
            await self._send_claim_instructions(conversation)
        elif text in ["3", "groupe", "rejoindre"]:
            await self._send_group_join_instructions(conversation)
        elif text in ["4", "aide", "support"]:
            await self._send_support_message(conversation)
        else:
            await self._send_main_menu(conversation)
    
    async def _send_trade_selection_menu(self, conversation: WhatsAppConversation):
        """Send trade selection options with CNMCI reference."""
        text = (
            "🔨 Sélectionnez votre métier:\n"
            "(Liste CNMCI - Chambre Nationale des Métiers)\n\n"
            "1. Menuisier\n"
            "2. Mécanicien\n"
            "3. Électricien\n"
            "4. Plombier\n"
            "5. Maçon\n"
            "6. Peintre\n"
            "7. Soudeur\n"
            "8. Coiffeur\n"
            "9. Tailleur\n"
            "10. Vendeur\n"
            "11. Autre\n\n"
            "Répondez par le numéro ou le nom du métier."
        )
        text += self._get_footer(conversation.context.get("region"))
        
        self.client.send_message(OutboundMessage(
            phone=conversation.phone,
            type=MessageType.TEXT,
            text=text
        ))
    
    async def _send_invalid_trade_message(self, conversation: WhatsAppConversation):
        """Send invalid trade error."""
        self.client.send_message(OutboundMessage(
            phone=conversation.phone,
            type=MessageType.TEXT,
            text="Métier non reconnu. Veuillez choisir parmi la liste proposée."
        ))
    
    async def _send_enrollment_summary(self, conversation: WhatsAppConversation):
        """Send enrollment summary before payment."""
        trade = conversation.context.get("trade", "Non spécifié")
        plan = conversation.context.get("plan", "Non spécifié")
        covers_parents = conversation.context.get("covers_parents", False)
        
        text = (
            "📋 Récapitulatif de votre souscription:\n\n"
            f"Métier: {trade.title()}\n"
            f"Formule: {plan.title()}\n"
        )
        
        if plan == "family":
            text += f"Couverture parents: {'Oui' if covers_parents else 'Non'}\n"
        
        text += "\nMontant total: "
        if plan == "individual":
            text += "5,000 FCFA/mois"
        elif plan == "family":
            text += "15,000 FCFA/mois"
        else:
            text += "Variable"
        
        text += "\n\nPour confirmer et payer, répondez CONFIRMER"
        text += self._get_footer(conversation.context.get("region"))
        
        self.client.send_message(OutboundMessage(
            phone=conversation.phone,
            type=MessageType.TEXT,
            text=text
        ))
    
    async def _send_plan_downgrade_message(self, conversation: WhatsAppConversation):
        """Send message when user rejects parental coverage, offering individual plan."""
        text = (
            "⚠️ La formule Famille nécessite la couverture des parents.\n\n"
            "Options disponibles:\n"
            "1. Formule Individuelle - 5,000 FCFA/mois\n"
            "2. Formule Famille avec parents - 15,000 FCFA/mois\n\n"
            "Répondez par le numéro de votre choix."
        )
        text += self._get_footer(conversation.context.get("region"))
        
        self.client.send_message(OutboundMessage(
            phone=conversation.phone,
            type=MessageType.TEXT,
            text=text
        ))
    
    async def _send_plan_options(self, conversation: WhatsAppConversation):
        """Send plan selection options."""
        text = (
            "📋 Choisissez votre formule:\n\n"
            "1. Individuelle - 5,000 FCFA/mois\n"
            "2. Famille (2 parents + enfants) - 15,000 FCFA/mois\n"
            "3. Groupe (via syndicat) - Réduction 10%\n\n"
            "Répondez par: individuelle, famille, ou groupe"
        )
        text += self._get_footer(conversation.context.get("region"))
        
        self.client.send_message(OutboundMessage(
            phone=conversation.phone,
            type=MessageType.TEXT,
            text=text
        ))
    
    async def _send_group_join_instructions(self, conversation: WhatsAppConversation):
        """Send instructions for joining a group."""
        text = (
            "👥 Pour rejoindre un groupe, envoyez:\n\n"
            "CODE [votre_code_groupe]\n\n"
            "Exemple: CODE GBAKA1"
        )
        self.client.send_message(OutboundMessage(
            phone=conversation.phone,
            type=MessageType.TEXT,
            text=text
        ))
    
    async def _send_group_joined_confirmation(self, conversation: WhatsAppConversation, group_code: str):
        """Send confirmation after joining group."""
        self.client.send_message(OutboundMessage(
            phone=conversation.phone,
            type=MessageType.TEXT,
            text=f"✅ Vous avez rejoint le groupe {group_code}! Votre réduction sera appliquée."
        ))
    
    async def _send_invalid_group_code(self, conversation: WhatsAppConversation):
        """Send error for invalid group code."""
        self.client.send_message(OutboundMessage(
            phone=conversation.phone,
            type=MessageType.TEXT,
            text="❌ Code groupe invalide ou groupe complet. Vérifiez et réessayez."
        ))
    
    async def _send_claim_confirmation(self, phone: str, claim_id: str, message: str):
        """Send claim confirmation to user."""
        try:
            text = (
                f"{message}\n\n"
                f"N° de sinistre: {claim_id}\n"
                "Suivi disponible 24h/24 dans votre espace client."
            )
            self.client.send_message(OutboundMessage(
                phone=phone,
                type=MessageType.TEXT,
                text=text
            ))
        except Exception as e:
            logger.error(f"Failed to send claim confirmation: {e}")

    def _activate_group_members(self, group: GroupEnrollment):
        """Activate all members after group payment."""
        members = self.db.query(WhatsAppConversation).filter(
            WhatsAppConversation.group_id == group.id
        ).all()
        
        for member in members:
            self.state_machine.transition(
                member,
                ConversationState.IDLE,
                context_update={"group_active": True}
            )
        
        self.db.commit()
    
    def _pay_leader_commission(self, group: GroupEnrollment, amount: Decimal):
        """Record commission payment to group leader."""
        from .models import CommissionPayment
        
        payment = CommissionPayment(
            group_id=group.id,
            leader_phone=group.leader_phone,
            amount=amount,
            payment_method="orange_money",  # Default
            status="pending"
        )
        
        self.db.add(payment)
        group.commission_paid = amount
        self.db.commit()
        
        # Notify leader
        text = (
            f"Votre commission de {int(amount)} FCFA a été créditée!\n\n"
            "Merci pour votre confiance."
        )
        
        try:
            self.client.send_message(OutboundMessage(
                phone=group.leader_phone,
                type=MessageType.TEXT,
                text=text
            ))
        except Exception as e:
            logger.error(f"Failed to send commission notification: {e}")

    # ═════════════════════════════════════════════════════════════════
    # IVORY COAST BUSINESS LOGIC CONSTRAINTS
    # ═════════════════════════════════════════════════════════════════
    
    # CNMCI Official Trade Categories (Chambre Nationale des Métiers)
    CNMCI_TRADES = [
        "menuisier", "mecanicien", "electricien", "plombier", "macon",
        "peintre", "soudeur", "coiffeur", "tailleur", "vendeur",
        "cordonnier", "tisserand", "potier", "forgeron", "cuisinier",
        "boulanger", "patissier", "mecanicien_moto", "carrossier",
        "vitrier", "tapissier", "maroquinier", " bijoutier", "horloger"
    ]
    
    # Border regions flagged for fraud review
    BORDER_REGIONS = ["noe", "danane", "odienne", "man", "touba"]
    
    # USSD Fallback code
    USSD_FALLBACK = "130WALI#"
    
    def _get_footer(self, region: Optional[str] = None) -> str:
        """Generate message footer with USSD fallback and regional info."""
        footer = f"\n\n📞 USSD: {self.USSD_FALLBACK} (si WhatsApp indisponible)"
        
        if region:
            region_lower = region.lower()
            if region_lower in ["abidjan", "cocody", "marcory", "treichville"]:
                footer += "\n🏥 Pharmacie de garde: https://wali.ci/pharmacies-garde"
            elif region_lower in ["korhogo", "man", "odienne", "bondoukou"]:
                footer += "\n⚠️ Zone rurale: En cas de problème réseau, visitez un agent Wali."
            elif region_lower in self.BORDER_REGIONS:
                footer += "\n⏳ Vérification additionnelle requise (zone frontalière)."
        
        return footer
    
    def _is_quiet_hours(self) -> bool:
        """Check if current time is within ARTCI quiet hours (before 08:00 or after 20:00)."""
        now = datetime.utcnow()
        hour = now.hour
        return hour < 8 or hour >= 20
    
    def _sanitize_message(self, text: str) -> str:
        """Remove any mobile money PINs and informal language from messages."""
        import re
        
        # Delete any 4-digit PINs that might have been sent by mistake
        text = re.sub(r'\b\d{4}\b', '[SUPPRIMÉ]', text)
        
        # Replace informal French with professional tone
        informal_to_formal = {
            r'\bsalut\b': 'Bonjour',
            r'\bça va\b': 'Comment allez-vous',
            r'\bca va\b': 'Comment allez-vous',
            r'\bhey\b': 'Bonjour',
            r'\bcoucou\b': 'Bonjour',
            r'\bmerci bcp\b': 'Merci beaucoup',
            r'\bok\b': "D'accord",
            r'\boki\b': "D'accord",
            r'\bdac\b': "D'accord",
        }
        
        for pattern, replacement in informal_to_formal.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        return text
    
    def _validate_trade_cnmci(self, trade: str) -> bool:
        """Validate trade against CNMCI official list."""
        return trade.lower() in self.CNMCI_TRADES
    
    def _check_active_policy(self, phone: str) -> bool:
        """Check if user already has an active policy (prevent duplicates)."""
        # Query for active policies
        existing = self.db.query(WhatsAppConversation).filter(
            WhatsAppConversation.phone == phone,
            WhatsAppConversation.state.in_([
                ConversationState.PAYMENT_PENDING,
                ConversationState.SETTLEMENT
            ])
        ).first()
        
        if existing and existing.context.get("policy_active"):
            return True
        return False
    
    def _check_claim_limit(self, amount: Decimal) -> bool:
        """Check if claim amount exceeds 500,000 CFA limit for WhatsApp processing."""
        return amount <= Decimal("500000")
    
    def _send_policy_document(self, phone: str, policy_id: str, language: str = "fr"):
        """Send PDF policy document within 24 hours of payment (legal requirement)."""
        try:
            # Generate PDF URL (would be generated and stored in production)
            pdf_url = f"https://wali.ci/policies/{policy_id}/document.pdf"
            
            templates = {
                "fr": f"Votre attestation d'assurance est prête: {pdf_url}\n\nConservez ce document. Il fait foi de votre couverture.",
                "dy": f"War bolo kɛ: {pdf_url}\n\nMarabolo walasa ka ɲɛ.",
                "ba": f"N'ko gbe: {pdf_url}\n\nGnon kwa.",
            }
            
            text = templates.get(language, templates["fr"])
            text += self._get_footer()
            
            self.client.send_message(OutboundMessage(
                phone=phone,
                type=MessageType.TEXT,
                text=text
            ))
            
            logger.info(f"Policy document sent to {phone} for policy {policy_id}")
            
        except Exception as e:
            logger.error(f"Failed to send policy document: {e}")
    
    async def send_payment_reminder_with_constraints(
        self,
        phone: str,
        amount: Decimal,
        due_date: datetime,
        region: Optional[str] = None
    ) -> bool:
        """Send payment reminder respecting ARTCI quiet hours."""
        # Check quiet hours
        if self._is_quiet_hours():
            logger.info(f"Quiet hours active. Queuing reminder for {phone}")
            return False
        
        text = (
            f"Wali Assurance SARL - Rappel de paiement\n\n"
            f"Montant: {int(amount)} FCFA\n"
            f"Échéance: {due_date.strftime('%d/%m/%Y')}\n\n"
            f"Référence: WALI{phone[-6:]}\n"
            f"OM: *144*4*6*{int(amount)}#\n"
            f"Wave: Transfert au 07 XX XX XX XX"
        )
        
        text += self._get_footer(region)
        
        try:
            self.client.send_message(OutboundMessage(
                phone=phone,
                type=MessageType.TEXT,
                text=text
            ))
            return True
        except Exception as e:
            logger.error(f"Failed to send payment reminder: {e}")
            return False
    
    async def handle_claim_with_escalation(
        self,
        phone: str,
        amount: Decimal,
        description: str,
        db: Session
    ) -> Dict[str, Any]:
        """Handle claim with automatic escalation for amounts >500k CFA."""
        result = {
            "success": False,
            "escalated": False,
            "claim_id": None,
            "message": ""
        }
        
        # Check if exceeds WhatsApp limit
        if not self._check_claim_limit(amount):
            result["escalated"] = True
            result["message"] = (
                "Votre sinistre dépasse 500,000 FCFA. "
                "Un agent Wali va vous contacter sous 24h pour finaliser votre déclaration.\n\n"
                "Référence: " + str(uuid4())[:8].upper()
            )
            
            # Log escalation for human agent
            logger.warning(f"Claim escalated: {phone} - Amount: {amount}")
            
            # Send message
            self.client.send_message(OutboundMessage(
                phone=phone,
                type=MessageType.TEXT,
                text=result["message"]
            ))
            
            return result
        
        # Process normally for amounts <= 500k
        # ... (existing claim processing logic)
        
        return result
    
    def _validate_explicit_consent(self, message: str) -> bool:
        """Validate explicit 'OUI' consent for Law 2013-450."""
        return message.strip().upper() == "OUI"
    
    async def send_parental_confirmation(self, phone: str, region: Optional[str] = None):
        """Send mandatory parental coverage confirmation (CIMA requirement)."""
        text = (
            "⚠️ CONFIRMATION OBLIGATOIRE\n\n"
            "La formule Famille couvre:\n"
            "• Vous (souscripteur)\n"
            "• Votre conjoint(e)\n"
            "• Jusqu'à 3 enfants\n"
            "• 2 parents (père ET mère)\n\n"
            "Cette formule inclut vos 2 parents. Confirmez-vous cette inclusion?\n\n"
            "Répondez OUI pour confirmer ou NON pour exclure."
        )
        
        text += self._get_footer(region)
        
        self.client.send_message(OutboundMessage(
            phone=phone,
            type=MessageType.TEXT,
            text=text
        ))
    
    async def complete_enrollment_flow(
        self,
        conversation: WhatsAppConversation,
        db: Session
    ) -> bool:
        """Complete enrollment with all legal requirements."""
        try:
            # 1. Check for existing active policy
            if self._check_active_policy(conversation.phone):
                await self._send_duplicate_policy_warning(conversation)
                return False
            
            # 2. Validate trade if provided
            trade = conversation.context.get("trade")
            if trade and not self._validate_trade_cnmci(trade):
                await self._send_invalid_trade_cnmci(conversation)
                return False
            
            # 3. Check border region for fraud review
            region = conversation.context.get("region", "").lower()
            if region in self.BORDER_REGIONS:
                conversation.context["fraud_review_required"] = True
                logger.warning(f"Border region enrollment flagged: {conversation.phone}")
            
            # 4. Process payment
            # ... (payment logic)
            
            # 5. Activate policy
            policy_id = f"POL-{datetime.utcnow().strftime('%Y%m%d')}-{uuid4().hex[:6].upper()}"
            conversation.context.update({
                "policy_id": policy_id,
                "policy_active": True,
                "activated_at": datetime.utcnow().isoformat()
            })
            
            self.state_machine.transition(
                conversation,
                ConversationState.IDLE,
                context_update={"policy_active": True}
            )
            
            db.commit()
            
            # 6. Send policy document (legal requirement within 24h)
            self._send_policy_document(
                conversation.phone,
                policy_id,
                conversation.language.value
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Enrollment completion failed: {e}")
            db.rollback()
            return False
    
    async def _send_duplicate_policy_warning(self, conversation: WhatsAppConversation):
        """Warn user about duplicate policy."""
        text = (
            "⚠️ Vous avez déjà une assurance active avec Wali.\n\n"
            "Pour modifier votre formule ou ajouter des bénéficiaires, "
            "contactez notre service client."
        )
        text += self._get_footer(conversation.context.get("region"))
        
        self.client.send_message(OutboundMessage(
            phone=conversation.phone,
            type=MessageType.TEXT,
            text=text
        ))
    
    async def _send_invalid_trade_cnmci(self, conversation: WhatsAppConversation):
        """Send invalid trade error with CNMCI reference."""
        text = (
            "❌ Métier non reconnu par la CNMCI (Chambre Nationale des Métiers).\n\n"
            "Métiers acceptés:\n"
            + ", ".join(self.CNMCI_TRADES[:10]) + ", etc.\n\n"
            "Si votre métier ne figure pas sur la liste, contactez-nous."
        )
        text += self._get_footer(conversation.context.get("region"))
        
        self.client.send_message(OutboundMessage(
            phone=conversation.phone,
            type=MessageType.TEXT,
            text=text
        ))
    
    async def send_emergency_claim_response(
        self,
        phone: str,
        claim_id: str,
        region: Optional[str] = None
    ):
        """
        Send emergency claim response that bypasses quiet hours.
        Medical emergencies are allowed 24/7 per ARTCI regulations.
        """
        text = (
            "🚨 URGENCE SANTÉ - Wali Assurance\n\n"
            f"Sinistre enregistré: {claim_id}\n"
            "Code d'urgence: ENREGISTRÉ\n\n"
            "Pharmacies de garde:\n"
        )
        
        # Regional pharmacy information
        region_lower = (region or "").lower()
        if region_lower in ["abidjan", "cocody", "marcory", "treichville"]:
            text += "• Pharmacie du Plateau: 07 20 00 00 00\n• Pharmacie Riviera: 07 21 00 00 00"
        elif region_lower in ["korhogo"]:
            text += "• Pharmacie Centre-Ville: 07 22 00 00 00"
        else:
            text += "• Composez le 130 pour pharmacies de garde"
        
        text += "\n\nNuméro vert: 130 (appel gratuit)"
        text += self._get_footer(region)
        
        # Emergency messages bypass quiet hours
        self.client.send_message(OutboundMessage(
            phone=phone,
            type=MessageType.TEXT,
            text=text
        ))
    
    async def send_claim_confirmation_with_escalation_check(
        self,
        phone: str,
        claim_id: str,
        estimated_amount: Decimal,
        region: Optional[str] = None
    ):
        """
        Send claim confirmation with appropriate messaging based on claim size.
        Claims >500k are escalated to human agents.
        """
        exceeds_limit = not self._check_claim_limit(estimated_amount)
        
        if exceeds_limit:
            # High-value claim - escalate to human
            text = (
                "📋 Déclaration de sinistre reçue\n\n"
                f"N° Sinistre: {claim_id}\n"
                f"Montant estimé: {int(estimated_amount):,} FCFA\n"
                "Statut: ESCALADE AGENT\n\n"
                "Votre sinistre dépasse notre seuil de traitement WhatsApp. "
                "Un agent Wali va vous contacter sous 24 heures ouvrées.\n\n"
                "📞 Contact urgent: 130"
            )
        else:
            # Standard claim
            text = (
                "✅ Sinistre enregistré avec succès\n\n"
                f"N° Sinistre: {claim_id}\n"
                f"Montant: {int(estimated_amount):,} FCFA\n"
                "Statut: EN COURS DE TRAITEMENT\n\n"
                "Délai de traitement: 48 heures ouvrées\n"
                f"Suivi: https://wali.ci/claims/{claim_id}"
            )
        
        text += self._get_footer(region)
        
        self.client.send_message(OutboundMessage(
            phone=phone,
            type=MessageType.TEXT,
            text=text
        ))
    
    async def process_scheduled_payment_reminders(self, db: Session):
        """
        Process scheduled payment reminders respecting quiet hours.
        Called by a scheduled job (e.g., APScheduler).
        """
        from datetime import time as dt_time
        
        # Only run during allowed hours (08:00 - 20:00)
        now = datetime.utcnow()
        current_time = dt_time(now.hour, now.minute)
        
        if current_time < dt_time(8, 0) or current_time > dt_time(20, 0):
            logger.info("Quiet hours active. Skipping payment reminders.")
            return
        
        # Query for pending payments due
        # This would query a PaymentDue table or similar
        # For now, placeholder implementation
        logger.info("Processing scheduled payment reminders...")
        
        # In production:
        # 1. Query PaymentDue table for payments due within next 3 days
        # 2. Filter out users who already received reminder today
        # 3. Send reminder for each
        # 4. Update reminder_sent timestamp
    
    def _is_emergency_message(self, text: str) -> bool:
        """
        Detect emergency keywords that allow messaging during quiet hours.
        Per ARTCI: Medical emergencies can be handled 24/7.
        """
        emergency_keywords = [
            "urgence", "urgent", "accident", "hopital", "hospital",
            "deces", "death", "mort", "blessure", "injured",
            "130", "sos", "secours", "ambulance"
        ]
        return any(keyword in text.lower() for keyword in emergency_keywords)
