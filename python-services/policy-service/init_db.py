import sys
import os

# Fix path for release command
sys.path.append(os.getcwd())

from app.core.database import engine
from app.models import (
    Base, Policy, User, Claim, PharmacyPartner,
    Partner, PartnerInvoice, PlatformUsageLog, PartnerApiConfig,
    FinancialEvent, PaydunyaTransaction, TaxExemptionTracking
)

def init_database():
    print("Initializing database...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    init_database()
