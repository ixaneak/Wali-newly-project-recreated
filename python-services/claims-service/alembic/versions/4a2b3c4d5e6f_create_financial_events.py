"""create financial_events audit table

Revision ID: 4a2b3c4d5e6f
Revises: 3a1b2c3d4e5f
Create Date: 2026-02-04

COSUMAF Compliance: Required audit trail for all financial transactions.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = '4a2b3c4d5e6f'
down_revision: Union[str, Sequence[str], None] = '3a1b2c3d4e5f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create financial_events table for COSUMAF compliance audit trail."""
    op.execute("""
        CREATE TABLE IF NOT EXISTS financial_events (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            transaction_id VARCHAR(100) UNIQUE NOT NULL,
            amount INTEGER NOT NULL,
            escrow_segregated BOOLEAN DEFAULT FALSE,
            compliance_hash VARCHAR(64),
            provider VARCHAR(50),
            policy_id UUID REFERENCES policies(id) ON DELETE SET NULL,
            user_id UUID REFERENCES users(id) ON DELETE SET NULL,
            status VARCHAR(20) DEFAULT 'pending',
            event_type VARCHAR(50) NOT NULL,
            metadata JSONB DEFAULT '{}',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        -- Index for fast transaction lookups
        CREATE INDEX IF NOT EXISTS idx_financial_events_transaction 
            ON financial_events(transaction_id);
        
        -- Index for compliance queries by date range
        CREATE INDEX IF NOT EXISTS idx_financial_events_created_at 
            ON financial_events(created_at);
        
        -- Index for policy-based lookups
        CREATE INDEX IF NOT EXISTS idx_financial_events_policy_id 
            ON financial_events(policy_id);
        
        -- Index for provider-based analytics
        CREATE INDEX IF NOT EXISTS idx_financial_events_provider 
            ON financial_events(provider);
        
        -- Trigger to auto-update updated_at
        CREATE OR REPLACE FUNCTION update_financial_events_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        
        DROP TRIGGER IF EXISTS trigger_financial_events_updated_at ON financial_events;
        CREATE TRIGGER trigger_financial_events_updated_at
            BEFORE UPDATE ON financial_events
            FOR EACH ROW
            EXECUTE FUNCTION update_financial_events_updated_at();
    """)


def downgrade() -> None:
    """Drop financial_events table and related objects."""
    op.execute("""
        DROP TRIGGER IF EXISTS trigger_financial_events_updated_at ON financial_events;
        DROP FUNCTION IF EXISTS update_financial_events_updated_at();
        DROP TABLE IF EXISTS financial_events;
    """)
