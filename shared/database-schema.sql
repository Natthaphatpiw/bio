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

-- ============================================
-- AI AGENT SYSTEM TABLES
-- Added for OpenAI Agents SDK Integration
-- ============================================

-- 4. Session Signals Table (Feature Store backup)
CREATE TABLE IF NOT EXISTS session_signals (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    session_id UUID REFERENCES verification_sessions(id) ON DELETE CASCADE,
    signal_type TEXT NOT NULL CHECK (signal_type IN ('integrity', 'lightsync', 'liveness', 'behavior', 'context')),
    raw_data JSONB NOT NULL,
    processed_score FLOAT,
    reason_codes TEXT[],

    -- Ensure one signal per type per session
    UNIQUE(session_id, signal_type)
);

-- 5. Agent Decisions Table
CREATE TABLE IF NOT EXISTS agent_decisions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    session_id UUID REFERENCES verification_sessions(id) ON DELETE CASCADE,

    -- Decision outcome
    decision TEXT NOT NULL CHECK (decision IN ('ALLOW', 'STEP_UP', 'HOLD', 'BLOCK')),
    final_risk FLOAT NOT NULL CHECK (final_risk >= 0 AND final_risk <= 1),
    reason_codes TEXT[] DEFAULT '{}',
    explanation TEXT,

    -- Evidence from each signal domain
    evidence JSONB DEFAULT '{}'::jsonb,

    -- Next action for mobile/ops
    next_action JSONB DEFAULT '{}'::jsonb,

    -- Audit trail
    audit JSONB DEFAULT '{}'::jsonb,

    -- Agent metadata
    agent_run_id TEXT,
    model_used TEXT DEFAULT 'gpt-5-mini',
    latency_ms FLOAT,
    token_usage JSONB DEFAULT '{}'::jsonb
);

-- 6. Fraud Cases Table
CREATE TABLE IF NOT EXISTS fraud_cases (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    session_id UUID REFERENCES verification_sessions(id) ON DELETE SET NULL,
    decision_id UUID REFERENCES agent_decisions(id) ON DELETE SET NULL,

    -- Case status
    status TEXT DEFAULT 'OPEN' CHECK (status IN ('OPEN', 'INVESTIGATING', 'CONFIRMED_FRAUD', 'FALSE_POSITIVE', 'CLOSED')),
    severity TEXT NOT NULL CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),

    -- Case details
    summary TEXT NOT NULL,
    evidence_refs JSONB DEFAULT '[]'::jsonb,
    recommended_action TEXT,

    -- Assignment
    assigned_to TEXT,
    assigned_at TIMESTAMP WITH TIME ZONE,

    -- Resolution
    resolution TEXT,
    resolved_by TEXT,
    resolved_at TIMESTAMP WITH TIME ZONE,

    -- Timeline and notes stored as JSONB arrays
    timeline JSONB DEFAULT '[]'::jsonb,
    notes JSONB DEFAULT '[]'::jsonb
);

-- 7. Copilot Conversations Table (for fraud investigation chat)
CREATE TABLE IF NOT EXISTS copilot_conversations (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    case_id UUID REFERENCES fraud_cases(id) ON DELETE CASCADE,

    -- Conversation
    user_id TEXT NOT NULL,
    messages JSONB DEFAULT '[]'::jsonb,

    -- Metadata
    last_message_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for AI Agent tables
CREATE INDEX idx_signals_session ON session_signals(session_id);
CREATE INDEX idx_signals_type ON session_signals(signal_type);
CREATE INDEX idx_decisions_session ON agent_decisions(session_id);
CREATE INDEX idx_decisions_decision ON agent_decisions(decision);
CREATE INDEX idx_decisions_risk ON agent_decisions(final_risk);
CREATE INDEX idx_cases_status ON fraud_cases(status);
CREATE INDEX idx_cases_severity ON fraud_cases(severity);
CREATE INDEX idx_cases_session ON fraud_cases(session_id);
CREATE INDEX idx_cases_assigned ON fraud_cases(assigned_to);
CREATE INDEX idx_copilot_case ON copilot_conversations(case_id);

-- Triggers for AI Agent tables
CREATE TRIGGER update_fraud_cases_updated_at
    BEFORE UPDATE ON fraud_cases
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Enable RLS on new tables
ALTER TABLE session_signals ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_decisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE fraud_cases ENABLE ROW LEVEL SECURITY;
ALTER TABLE copilot_conversations ENABLE ROW LEVEL SECURITY;

-- Service role policies for new tables
CREATE POLICY "Service role can do everything on signals" ON session_signals
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role can do everything on decisions" ON agent_decisions
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role can do everything on cases" ON fraud_cases
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role can do everything on copilot" ON copilot_conversations
    FOR ALL USING (auth.role() = 'service_role');

-- Enable Realtime for agent tables
ALTER PUBLICATION supabase_realtime ADD TABLE agent_decisions;
ALTER PUBLICATION supabase_realtime ADD TABLE fraud_cases;
