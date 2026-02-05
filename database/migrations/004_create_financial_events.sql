-- Create financial_events audit table for COSUMAF compliance
-- Run this via: flyctl postgres connect -a wali-db-dev -d wali < migrate_financial_events.sql

CREATE TABLE IF NOT EXISTS financial_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_id VARCHAR(100) UNIQUE NOT NULL,
    amount INTEGER NOT NULL,
    escrow_segregated BOOLEAN DEFAULT FALSE,
    compliance_hash VARCHAR(64),
    provider VARCHAR(50),
    policy_id UUID,
    user_id UUID,
    status VARCHAR(20) DEFAULT 'pending',
    event_type VARCHAR(50) NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add foreign keys if policies and users tables exist
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'policies') THEN
        ALTER TABLE financial_events 
        ADD CONSTRAINT fk_financial_events_policy 
        FOREIGN KEY (policy_id) REFERENCES policies(id) ON DELETE SET NULL;
    END IF;
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'users') THEN
        ALTER TABLE financial_events 
        ADD CONSTRAINT fk_financial_events_user 
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;
    END IF;
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_financial_events_transaction ON financial_events(transaction_id);
CREATE INDEX IF NOT EXISTS idx_financial_events_created_at ON financial_events(created_at);
CREATE INDEX IF NOT EXISTS idx_financial_events_policy_id ON financial_events(policy_id);
CREATE INDEX IF NOT EXISTS idx_financial_events_provider ON financial_events(provider);

-- Create auto-update trigger
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

-- Verify table was created
SELECT 'financial_events table created successfully' AS status;
\d financial_events
