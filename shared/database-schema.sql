-- BioGuard Nexus Database Schema
-- Run this in Supabase SQL Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Merchants Table (for multi-tenant support)
CREATE TABLE IF NOT EXISTS merchants (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    api_key TEXT UNIQUE NOT NULL DEFAULT encode(gen_random_bytes(32), 'hex'),
    webhook_url TEXT,
    is_active BOOLEAN DEFAULT true,
    settings JSONB DEFAULT '{
        "default_modules": ["environment", "light_sync", "face_liveness"],
        "webhook_enabled": false
    }'::jsonb
);

-- 2. Verification Sessions Table (main table)
CREATE TABLE IF NOT EXISTS verification_sessions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Merchant relationship
    merchant_id UUID REFERENCES merchants(id),
    merchant_name TEXT NOT NULL,

    -- Status
    status TEXT DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'IN_PROGRESS', 'COMPLETED', 'FAILED', 'EXPIRED')),

    -- Configuration
    config JSONB DEFAULT '{
        "check_emulator": true,
        "check_root": true,
        "check_hooking": true,
        "light_sync": true,
        "face_liveness": true
    }'::jsonb,

    -- Results from each module
    result JSONB,

    -- Webhook
    webhook_url TEXT,
    webhook_sent_at TIMESTAMP WITH TIME ZONE,

    -- Metadata
    user_agent TEXT,
    ip_address INET,
    device_info JSONB,

    -- Expiration
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() + INTERVAL '30 minutes'
);

-- 3. Audit Logs Table
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    session_id UUID REFERENCES verification_sessions(id),
    event_type TEXT NOT NULL,
    event_data JSONB,
    ip_address INET
);

-- Indexes for performance
CREATE INDEX idx_sessions_status ON verification_sessions(status);
CREATE INDEX idx_sessions_merchant ON verification_sessions(merchant_id);
CREATE INDEX idx_sessions_created ON verification_sessions(created_at DESC);
CREATE INDEX idx_audit_session ON audit_logs(session_id);

-- Enable Row Level Security
ALTER TABLE verification_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE merchants ENABLE ROW LEVEL SECURITY;

-- Policies (adjust based on your auth setup)
CREATE POLICY "Anyone can read pending sessions" ON verification_sessions
    FOR SELECT USING (status = 'PENDING');

CREATE POLICY "Service role can do everything" ON verification_sessions
    FOR ALL USING (auth.role() = 'service_role');

-- Enable Realtime
ALTER PUBLICATION supabase_realtime ADD TABLE verification_sessions;

-- Function to auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers
CREATE TRIGGER update_sessions_updated_at
    BEFORE UPDATE ON verification_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_merchants_updated_at
    BEFORE UPDATE ON merchants
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Function to expire old sessions
CREATE OR REPLACE FUNCTION expire_old_sessions()
RETURNS void AS $$
BEGIN
    UPDATE verification_sessions
    SET status = 'EXPIRED'
    WHERE status = 'PENDING' AND expires_at < NOW();
END;
$$ LANGUAGE plpgsql;
