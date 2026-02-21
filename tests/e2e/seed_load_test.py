import asyncio
import json
import random
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Import from policy service context 
# We assume this script runs inside the app container or with proper PYTHONPATH
from app.models.base import Base # Adjust if your actual import path differs
from app.models.policy import Artisan, CoverageSubscription, PolicyStatus, CoverageType
from app.models.pharmacy import Pharmacy
from app.models.claims import Claim, ClaimStatus

# Need the async standard db connect but we can just make our own for isolation
DATABASE_URL = "postgresql+asyncpg://user:pass@localhost:5432/wali" # Overridden by env var in real usage
# We default to local DB for script running directly, but in Docker we use env
import os
DB_URL = os.getenv("DATABASE_URL", DATABASE_URL)

engine = create_async_engine(DB_URL, echo=False)
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

def generate_ivorian_phone():
    """Generate typical +225 07 XX XX XX XX number"""
    return f"+22507{random.randint(10000000, 99999999)}"

def random_abidjan_point():
    """Return realistic Abidjan coordinates bounding box"""
    return {
        "lat": 5.2 + (random.random() * 0.2),
        "lng": -4.1 + (random.random() * 0.2)
    }

async def clear_database(session: AsyncSession):
    """Truncate the specific tables used for testing before we seed to remain idempotent."""
    print("Clearing tables...")
    await session.execute(text("TRUNCATE TABLE claims CASCADE;"))
    await session.execute(text("TRUNCATE TABLE coverage_subscriptions CASCADE;"))
    await session.execute(text("TRUNCATE TABLE artisans CASCADE;"))
    await session.execute(text("TRUNCATE TABLE pharmacies CASCADE;"))
    await session.commit()

async def seed_data():
    output_path = Path("tests/load/test_credentials.json")
    
    test_credentials = {
        "artisans": [],
        "pharmacies": [],
        "policies": []
    }
    
    async with AsyncSessionLocal() as session:
        await clear_database(session)
        print("Database cleared.")
        
        # 1. Seed 500 Pharmacies
        print("Seeding 500 pharmacies...")
        tzinfo = timezone.utc
        pharmacies = []
        
        # specific requested coordinates
        specific_locations = [
            {"name": "Pharmacie Cocody TEST", "lat": 5.3415, "lng": -3.9920},
            {"name": "Pharmacie Treichville TEST", "lat": 5.3000, "lng": -4.0000},
            {"name": "Pharmacie Plateau TEST", "lat": 5.3200, "lng": -4.0200},
            {"name": "Pharmacie Bouake TEST", "lat": 7.6900, "lng": -5.0300},
            {"name": "Pharmacie Yamoussoukro TEST", "lat": 6.8200, "lng": -5.2800}
        ]
        
        for i in range(500):
            if i < 5:
                # Use specified
                loc = specific_locations[i]
                lat, lng = loc["lat"], loc["lng"]
                name = loc["name"]
            else:
                loc = random_abidjan_point()
                lat, lng = loc["lat"], loc["lng"]
                name = f"Pharmacie Abidjan TEST {i}"
                
            p_phone = generate_ivorian_phone()
            pharmacy = Pharmacy(
                id=uuid.uuid4(),
                name=name,
                rccm=f"CI-ABJ-TEST-{random.randint(10000, 99999)}",
                phone=p_phone,
                payment_phone=p_phone,
                wallet_balance=0.0,
                latitude=lat,
                longitude=lng,
                is_active=True,
                created_at=datetime.now(tzinfo)
            )
            pharmacies.append(pharmacy)
            test_credentials["pharmacies"].append({"id": str(pharmacy.id), "phone": p_phone})
            
            if len(pharmacies) >= 100:
                session.add_all(pharmacies)
                await session.flush()
                pharmacies = []
                
        if pharmacies:
            session.add_all(pharmacies)
            await session.flush()
            
        # 2. Seed 10,000 Artisans + Subscriptions
        print("Seeding 10,000 artisans and active policies...")
        artisans = []
        subscriptions = []
        batch_size = 500
        
        now = datetime.now(tzinfo)
        one_year_from_now = now + timedelta(days=365)
        
        for i in range(10000):
            a_phone = generate_ivorian_phone()
            artisan = Artisan(
                id=uuid.uuid4(),
                firebase_uid=f"fake_firebase_uid_{uuid.uuid4().hex[:8]}", # 10k unique fakes
                first_name=f"TestArtisan{i}",
                last_name="WaliLoadTest",
                phone=a_phone,
                profession="Menuisier",
                created_at=now
            )
            artisans.append(artisan)
            
            # 80% have active policies
            is_active = random.random() < 0.8
            if is_active:
                sub = CoverageSubscription(
                    id=uuid.uuid4(),
                    artisan_id=artisan.id,
                    coverage_type=CoverageType.INDIVIDUAL,
                    status=PolicyStatus.ACTIVE,
                    start_date=now - timedelta(days=random.randint(10, 100)),
                    end_date=one_year_from_now,
                    wallet_balance=0.0
                )
                subscriptions.append(sub)
                
                # We need exact policy IDs for the K6 tests to make QR codes
                if len(test_credentials["policies"]) < 1000:
                     test_credentials["policies"].append({"id": str(sub.id), "artisan_id": str(artisan.id)})

            if len(artisans) >= batch_size:
                session.add_all(artisans)
                session.add_all(subscriptions)
                await session.flush()
                artisans = []
                subscriptions = []
                print(f"  ... inserted batch up to {i}")
                
        if artisans:
            session.add_all(artisans)
            session.add_all(subscriptions)
            await session.flush()
            
        print("Saving test credentials output JSON...")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(test_credentials, f, indent=2)
            
        await session.commit()
        print("Seed complete.")
        
if __name__ == "__main__":
    asyncio.run(seed_data())
