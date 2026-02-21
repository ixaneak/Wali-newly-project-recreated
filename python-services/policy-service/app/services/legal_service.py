from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import re
from app.models.legal import LegalConfig, LegalTemplate, DocumentType
from fastapi import HTTPException

class LegalService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_config(self) -> LegalConfig:
        result = await self.db.execute(select(LegalConfig).limit(1))
        config = result.scalars().first()
        if not config:
            # Fallback or initialized empty for dev
            return LegalConfig(
                rccm="CI-ABJ-123456",
                cc="1234567 A",
                email_dpo="dpo@wali.ci",
                artci_authorization="ARTCI-2025-001"
            )
        return config

    async def render_template(self, doc_type: DocumentType, user_data: dict) -> str:
        result = await self.db.execute(
            select(LegalTemplate).where(LegalTemplate.doc_type == doc_type, LegalTemplate.is_active == True)
        )
        template = result.scalars().first()
        if not template:
            raise HTTPException(status_code=404, detail=f"Template {doc_type} not found")

        content = template.content
        config = await self.get_config()
        
        # Merge system config with user data
        placeholders = {
            "rccm": config.rccm,
            "cc": config.cc,
            "email_dpo": config.email_dpo,
            "artci_authorization": config.artci_authorization,
            **user_data
        }

        # Replace placeholders matching {{ key }}
        def replace_match(match):
            key = match.group(1).strip()
            return str(placeholders.get(key, f"{{{{{key}}}}}"))

        rendered_content = re.sub(r'\{\{\s*(\w+)\s*\}\}', replace_match, content)
        return rendered_content
