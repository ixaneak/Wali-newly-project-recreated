-- ==========================================
-- Wali Backend - Initial Database Schema
-- PostgreSQL 15+ with PostGIS Extension
-- ==========================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==========================================
-- ENUMS
-- ==========================================

CREATE TYPE user_role AS ENUM ('artisan', 'pharmacy', 'admin');
CREATE TYPE kyc_status AS ENUM ('pending', 'verified', 'rejected');
CREATE TYPE policy_status AS ENUM ('pending', 'active', 'suspended', 'cancelled');
CREATE TYPE payment_provider AS ENUM ('orange', 'mtn', 'wave');
CREATE TYPE transaction_status AS ENUM ('pending', 'success', 'failed', 'refunded');
CREATE TYPE claim_status AS ENUM ('submitted', 'under_review', 'approved', 'rejected', 'paid');
CREATE TYPE coverage_type AS ENUM ('health', 'equipment', 'theft', 'bundle');
CREATE TYPE payment_frequency AS ENUM ('daily', 'weekly', 'monthly');
CREATE TYPE event_type AS ENUM ('premium_collected', 'claim_paid', 'tech_fee', 'refund');

-- ==========================================
-- USERS TABLE
-- ==========================================

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phone VARCHAR(20) UNIQUE NOT NULL,
    role user_role NOT NULL,
    kyc_status kyc_status DEFAULT 'pending',
    provider_preference payment_provider,
    
    -- Artisan-specific fields
    nui VARCHAR(50),  -- CNPS Numéro d'Identifiant Unique
    profession VARCHAR(100),
    region VARCHAR(100),
    
    -- Pharmacy-specific fields
    license_number VARCHAR(100),
    pharmacy_name VARCHAR(200),
    
    -- Security
    hashed_password VARCHAR(255),
    fingerprint_hash VARCHAR(255),  -- For biometric auth
    last_login TIMESTAMP,
    imsi VARCHAR(50),  -- For SIM swap detection
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP,
    
    CONSTRAINT valid_phone CHECK (phone ~ '^\+225[0-9]{10}$')
);

CREATE INDEX idx_users_phone ON users(phone);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_nui ON users(nui) WHERE nui IS NOT NULL;

-- ==========================================
-- PHARMACIES TABLE (Geospatial)
-- ==========================================

CREATE TABLE pharmacies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    license_number VARCHAR(100) UNIQUE NOT NULL,
    pharmacy_name VARCHAR(200) NOT NULL,
    location GEOGRAPHY(POINT, 4326),  -- WGS84 coordinates
    address TEXT,
    city VARCHAR(100),
    region VARCHAR(100),
    supported_payment_methods payment_provider[],
    operating_hours JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_pharmacies_location ON pharmacies USING GIST(location);
CREATE INDEX idx_pharmacies_user ON pharmacies(user_id);

-- ==========================================
-- POLICIES TABLE
-- ==========================================

CREATE TABLE policies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    policy_number VARCHAR(50) UNIQUE NOT NULL,
    coverage_type coverage_type NOT NULL,
    coverage_details JSONB NOT NULL,  -- Flexible micro-insurance terms
    premium_amount INTEGER NOT NULL,  -- XOF as integer (no floats)
    payment_frequency payment_frequency NOT NULL,
    status policy_status DEFAULT 'pending',
    
    -- Payment tracking
    mobile_money_ref VARCHAR(100),
    last_payment_date TIMESTAMP,
    next_payment_date TIMESTAMP,
    
    -- Policy lifecycle
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    cancellation_reason TEXT,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT positive_premium CHECK (premium_amount > 0),
    CONSTRAINT valid_dates CHECK (end_date IS NULL OR end_date > start_date)
);

CREATE INDEX idx_policies_user ON policies(user_id);
CREATE INDEX idx_policies_status ON policies(status);
CREATE INDEX idx_policies_next_payment ON policies(next_payment_date) WHERE status = 'active';

-- ==========================================
-- TRANSACTIONS TABLE
-- ==========================================

CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    policy_id UUID REFERENCES policies(id) ON DELETE SET NULL,
    
    -- Payment details
    provider payment_provider NOT NULL,
    transaction_ref VARCHAR(100) UNIQUE NOT NULL,
    amount INTEGER NOT NULL,
    status transaction_status DEFAULT 'pending',
    
    -- Retry logic
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    next_retry_at TIMESTAMP,
    
    -- Provider response
    provider_response JSONB,
    error_message TEXT,
    
    -- Idempotency
    idempotency_key VARCHAR(100) UNIQUE,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    
    CONSTRAINT positive_amount CHECK (amount > 0),
    CONSTRAINT valid_retry CHECK (retry_count <= max_retries)
);

CREATE INDEX idx_transactions_user ON transactions(user_id);
CREATE INDEX idx_transactions_provider ON transactions(provider);
CREATE INDEX idx_transactions_status ON transactions(status);
CREATE INDEX idx_transactions_idempotency ON transactions(idempotency_key);
CREATE INDEX idx_transactions_retry ON transactions(next_retry_at) WHERE status = 'pending' AND retry_count < max_retries;

-- ==========================================
-- CLAIMS TABLE
-- ==========================================

CREATE TABLE claims (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    policy_id UUID REFERENCES policies(id) ON DELETE CASCADE,
    claim_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- Claim details
    claim_type coverage_type NOT NULL,
    description TEXT NOT NULL,
    claimed_amount INTEGER NOT NULL,
    approved_amount INTEGER,
    
    -- Documentation
    image_urls TEXT[],
    image_hashes TEXT[],  -- Perceptual hashes for fraud detection
    exif_data JSONB,
    
    -- Status
    status claim_status DEFAULT 'submitted',
    reviewer_id UUID REFERENCES users(id),
    review_notes TEXT,
    
    -- Payout
    payout_transaction_id UUID REFERENCES transactions(id),
    payout_date TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    reviewed_at TIMESTAMP,
    
    CONSTRAINT positive_claimed_amount CHECK (claimed_amount > 0),
    CONSTRAINT valid_approved_amount CHECK (approved_amount IS NULL OR approved_amount >= 0)
);

CREATE INDEX idx_claims_user ON claims(user_id);
CREATE INDEX idx_claims_policy ON claims(policy_id);
CREATE INDEX idx_claims_status ON claims(status);
CREATE INDEX idx_claims_created ON claims(created_at);

-- ==========================================
-- FINANCIAL EVENTS TABLE (Immutable Audit Log)
-- ==========================================

CREATE TABLE financial_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type event_type NOT NULL,
    amount INTEGER NOT NULL,
    
    -- Tax compliance
    segregated_escrow BOOLEAN NOT NULL,  -- True for premiums, False for tech fees
    escrow_account VARCHAR(100),  -- BCEAO-certified account
    
    -- References
    transaction_id UUID REFERENCES transactions(id),
    policy_id UUID REFERENCES policies(id),
    claim_id UUID REFERENCES claims(id),
    user_id UUID REFERENCES users(id),
    
    -- Blockchain-style hashing for tamper-evidence
    previous_hash VARCHAR(64),
    compliance_hash VARCHAR(64) NOT NULL,  -- SHA-256(event_data + previous_hash)
    
    -- Metadata
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    
    CONSTRAINT positive_event_amount CHECK (amount > 0)
);

CREATE INDEX idx_financial_events_type ON financial_events(event_type);
CREATE INDEX idx_financial_events_escrow ON financial_events(segregated_escrow);
CREATE INDEX idx_financial_events_created ON financial_events(created_at);
CREATE INDEX idx_financial_events_transaction ON financial_events(transaction_id);

-- ==========================================
-- AUDIT LOG TABLE
-- ==========================================

CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id UUID,
    ip_address INET,
    user_agent TEXT,
    changes JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_audit_log_user ON audit_log(user_id);
CREATE INDEX idx_audit_log_action ON audit_log(action);
CREATE INDEX idx_audit_log_created ON audit_log(created_at);

-- ==========================================
-- VELOCITY CHECKS TABLE (Fraud Prevention)
-- ==========================================

CREATE TABLE velocity_checks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    check_type VARCHAR(50) NOT NULL,  -- 'policy_changes', 'failed_logins', 'claims'
    count INTEGER DEFAULT 1,
    window_start TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_velocity_user_type ON velocity_checks(user_id, check_type);
CREATE INDEX idx_velocity_window ON velocity_checks(window_start);

-- ==========================================
-- FUNCTIONS & TRIGGERS
-- ==========================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_policies_updated_at BEFORE UPDATE ON policies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_transactions_updated_at BEFORE UPDATE ON transactions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_claims_updated_at BEFORE UPDATE ON claims
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Generate policy number
CREATE OR REPLACE FUNCTION generate_policy_number()
RETURNS TRIGGER AS $$
BEGIN
    NEW.policy_number = 'WLI-' || TO_CHAR(NOW(), 'YYYYMMDD') || '-' || LPAD(nextval('policy_number_seq')::TEXT, 6, '0');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE SEQUENCE policy_number_seq;

CREATE TRIGGER set_policy_number BEFORE INSERT ON policies
    FOR EACH ROW WHEN (NEW.policy_number IS NULL)
    EXECUTE FUNCTION generate_policy_number();

-- Generate claim number
CREATE OR REPLACE FUNCTION generate_claim_number()
RETURNS TRIGGER AS $$
BEGIN
    NEW.claim_number = 'CLM-' || TO_CHAR(NOW(), 'YYYYMMDD') || '-' || LPAD(nextval('claim_number_seq')::TEXT, 6, '0');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE SEQUENCE claim_number_seq;

CREATE TRIGGER set_claim_number BEFORE INSERT ON claims
    FOR EACH ROW WHEN (NEW.claim_number IS NULL)
    EXECUTE FUNCTION generate_claim_number();

-- ==========================================
-- INITIAL DATA
-- ==========================================

-- Create admin user (password: Admin@2026)
INSERT INTO users (phone, role, kyc_status, hashed_password)
VALUES (
    '+22500000000',
    'admin',
    'verified',
    -- bcrypt hash of 'Admin@2026'
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMesrs.H5Y0.9WNSC1QSZ6q5u.'
);

-- Sample regions for Côte d'Ivoire
COMMENT ON COLUMN users.region IS 'Regions: Abidjan, Bouaké, Daloa, Korhogo, San-Pédro, Yamoussoukro, etc.';
