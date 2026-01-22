-- Initial schema for xScanner Studio
-- This migration creates the core tables for extraction management

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enforce extraction status values
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'extraction_status') THEN
        CREATE TYPE extraction_status AS ENUM (
            'pending',
            'validated',
            'corrected',
            'rejected',
            'error'
        );
    END IF;
END $$;

-- Extraction table: stores all extraction results with history
CREATE TABLE extraction (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Link to original extraction (for history tracking)
    original_id UUID NOT NULL,  -- References first version

    -- User who created this version
    updated_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,

    -- Image storage
    storage_path TEXT NOT NULL,  -- Relative path in bucket: "{original_id}/{uuid}.jpg"
    image_filename TEXT,  -- Original filename if provided (optional)

    -- Extraction metadata
    strategy_used TEXT NOT NULL, -- ChatGPT, Gemini, Hybrid, etc.
    confidence FLOAT,
    processing_time FLOAT,

    -- Extracted fields (normalized)
    serial_number TEXT,
    metal TEXT,
    weight TEXT,
    weight_unit TEXT,
    fineness TEXT,
    producer TEXT,

    -- Raw extracted data (flexible JSONB for all fields)
    extracted_data JSONB NOT NULL DEFAULT '{}',
    -- Example structure:
    -- {
    --   "SerialNumber": "123456",
    --   "Metal": "Gold",
    --   "Weight": "1000",
    --   "WeightUnit": "g",
    --   "Fineness": "999.9",
    --   "Producer": "Heraeus"
    -- }

    -- Status tracking
    status extraction_status NOT NULL DEFAULT 'pending', -- pending, validated, corrected, rejected, error

    -- Error handling
    error TEXT,

    -- Version control
    is_active BOOLEAN NOT NULL DEFAULT true,  -- Only one active version per original_id

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_extraction_updated_by ON extraction(updated_by);
CREATE INDEX idx_extraction_status ON extraction(status);
CREATE INDEX idx_extraction_created_at ON extraction(created_at DESC);
CREATE INDEX idx_extraction_strategy ON extraction(strategy_used);
CREATE INDEX idx_extraction_original_id ON extraction(original_id);
CREATE INDEX idx_extraction_is_active ON extraction(is_active);
CREATE INDEX idx_extraction_serial_number ON extraction(serial_number);
CREATE INDEX idx_extraction_metal ON extraction(metal);
CREATE INDEX idx_extraction_producer ON extraction(producer);
CREATE UNIQUE INDEX idx_extraction_active_per_original ON extraction(original_id) WHERE is_active = true;

-- GIN index for JSONB queries (enables fast searches in extracted_data)
CREATE INDEX idx_extraction_data ON extraction USING GIN (extracted_data);

-- Comments for documentation
COMMENT ON TABLE extraction IS 'Stores all barcode/bullion extraction results from xScanner with full history';
COMMENT ON COLUMN extraction.original_id IS 'References the first version of this extraction (groups all versions together)';
COMMENT ON COLUMN extraction.is_active IS 'Only one record per original_id should have is_active=true (enforced by unique index)';
COMMENT ON COLUMN extraction.extracted_data IS 'JSONB field containing all extracted fields (Metal, Weight, SerialNumber, etc.)';
COMMENT ON COLUMN extraction.status IS 'Workflow status: pending (needs review), validated (confirmed correct), corrected (manually fixed), rejected (discarded), error (extraction failed)';
