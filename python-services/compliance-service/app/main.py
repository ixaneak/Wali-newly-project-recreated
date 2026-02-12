"""
Wali Compliance Service — FastAPI Application.

B2B SaaS platform compliance, reporting, and audit trails.
Wali is a software vendor (NAF 6201Z), NOT an insurer or broker.
"""
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.core.config import get_settings
from app.core.database import engine, Base
from app.routes import compliance, dashboard
from app.models.financial_event import FinancialEvent
from app.models.tax_exemption import TaxExemptionTracking

Base.metadata.create_all(bind=engine)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_settings()

app = FastAPI(
    title="Wali Compliance Service",
    description=(
        "B2B SaaS platform compliance and audit trails. "
        "Wali is a software vendor (NAF 6201Z), NOT an insurer."
    ),
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(compliance.router)
app.include_router(dashboard.router)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "wali-compliance-service",
        "platform_model": "B2B_SAAS",
        "is_saas_platform": True,
        "is_insurer": False,
    }


@app.get("/")
def root():
    return {
        "service": "Wali Compliance Service",
        "version": "2.0.0",
        "model": "B2B_SAAS",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8002, reload=True)
