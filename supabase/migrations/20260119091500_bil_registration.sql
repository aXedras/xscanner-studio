-- Create BIL registration attempts table
-- Stores each attempt to register an extraction on aXedras Bullion Integrity Ledger (BIL)

CREATE TABLE IF NOT EXISTS bil_registration (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- FK to the specific extraction version that was attempted to be registered
    extraction_id UUID NOT NULL REFERENCES extraction(id) ON DELETE CASCADE,

    -- Where this registration was triggered from (e.g. auto from /extract or manual from /register)
    trigger_source TEXT NOT NULL,

    -- Result
    success BOOLEAN NOT NULL,
    certificate_id TEXT,

    -- Timing
    processing_time FLOAT,

    -- Error/diagnostics
    error TEXT,
    error_details JSONB,
    http_status INTEGER,
    endpoint TEXT,

    -- Payloads for audit/debugging
    payload_sent JSONB,
    payload_received JSONB,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_bil_registration_extraction_id ON bil_registration(extraction_id);
CREATE INDEX IF NOT EXISTS idx_bil_registration_created_at ON bil_registration(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_bil_registration_success ON bil_registration(success);

COMMENT ON TABLE bil_registration IS 'Stores BIL registration attempts for a specific extraction version';
COMMENT ON COLUMN bil_registration.extraction_id IS 'FK to extraction.id (the version that was attempted to be registered)';
