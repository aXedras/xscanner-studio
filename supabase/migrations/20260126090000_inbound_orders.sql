-- Orders (PDF) schema
-- Adds support for storing order/invoice PDFs and their extracted data.

-- 1) Allow PDFs in the existing private storage bucket.
-- We keep using the `extractions` bucket for now to avoid multi-bucket complexity.
UPDATE storage.buckets
SET allowed_mime_types = ARRAY(
    SELECT DISTINCT unnest(allowed_mime_types || ARRAY['application/pdf'])
)
WHERE id = 'extractions';

-- 2) Enforce allowed order status values
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'order_status') THEN
        CREATE TYPE order_status AS ENUM (
            'pending',
            'validated',
            'corrected',
            'rejected',
            'error'
            ,'closed'
        );
    END IF;
END $$;

-- Enforce allowed order document type values
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'order_document_type') THEN
        CREATE TYPE order_document_type AS ENUM (
            'invoice',
            'order_confirmation',
            'delivery_note',
            'unknown'
        );
    END IF;
END $$;

-- Enforce allowed bullion-related enums (used by order_item)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'bullion_metal') THEN
        CREATE TYPE bullion_metal AS ENUM (
            'gold',
            'silver',
            'platinum',
            'palladium',
            'unknown'
        );
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'bullion_weight_unit') THEN
        CREATE TYPE bullion_weight_unit AS ENUM (
            'g',
            'kg',
            'oz',
            'lb',
            'unknown'
        );
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'bullion_form') THEN
        CREATE TYPE bullion_form AS ENUM (
            'bar',
            'coin',
            'round',
            'unknown'
        );
    END IF;
END $$;

-- 3) Order table (versioned like extraction)
-- NOTE: "order" is a SQL keyword, so it must be quoted everywhere.
CREATE TABLE "order" (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Link to original order (for history tracking)
    original_id UUID NOT NULL,

    -- User who created this version
    updated_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,

    -- PDF storage (in Supabase Storage bucket `extractions` under a dedicated prefix)
    -- Suggested path: "orders/{original_id}/{id}.pdf"
    storage_path TEXT NOT NULL,
    pdf_filename TEXT,

    -- Canonical extracted fields (query-friendly; all other fields live in extracted_data)
    document_issuer TEXT NOT NULL,
    document_type order_document_type NOT NULL,
    document_number TEXT NOT NULL,
    document_date DATE NOT NULL,

    -- Trading metadata commonly present on invoices/order confirmations
    order_number TEXT,
    order_date DATE,
    value_date DATE,
    shipping_date DATE,
    transaction_type TEXT,

    -- Parties
    seller_name TEXT,
    buyer_name TEXT,

    -- Totals
    currency TEXT,
    shipping_charges_amount NUMERIC,
    other_charges_amount NUMERIC,
    subtotal_amount NUMERIC,
    total_amount NUMERIC,

    -- Extraction metadata
    strategy_used TEXT NOT NULL DEFAULT 'unknown',
    confidence FLOAT,
    processing_time FLOAT,

    -- structured extracted data
    extracted_data JSONB NOT NULL DEFAULT '{}',

    -- Status tracking
    status order_status NOT NULL DEFAULT 'pending',

    -- Error handling
    error TEXT,

    -- Version control
    is_active BOOLEAN NOT NULL DEFAULT true,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE "order"
ADD CONSTRAINT order_document_type_not_unknown
CHECK (document_type <> 'unknown');

ALTER TABLE "order"
ADD CONSTRAINT order_document_issuer_slug
CHECK (document_issuer ~ '^[a-z0-9]+(-[a-z0-9]+)*$');

-- Indexes
CREATE INDEX idx_order_updated_by ON "order"(updated_by);
CREATE INDEX idx_order_status ON "order"(status);
CREATE INDEX idx_order_created_at ON "order"(created_at DESC);
CREATE INDEX idx_order_strategy ON "order"(strategy_used);
CREATE INDEX idx_order_original_id ON "order"(original_id);
CREATE INDEX idx_order_is_active ON "order"(is_active);
CREATE INDEX idx_order_document_issuer ON "order"(document_issuer);
CREATE INDEX idx_order_document_type ON "order"(document_type);
CREATE INDEX idx_order_document_number ON "order"(document_number);
CREATE INDEX idx_order_document_date ON "order"(document_date);
CREATE INDEX idx_order_order_number ON "order"(order_number);
CREATE INDEX idx_order_order_date ON "order"(order_date);
CREATE INDEX idx_order_value_date ON "order"(value_date);
CREATE INDEX idx_order_shipping_date ON "order"(shipping_date);
CREATE INDEX idx_order_seller_name ON "order"(seller_name);
CREATE INDEX idx_order_buyer_name ON "order"(buyer_name);
CREATE UNIQUE INDEX idx_order_active_per_original ON "order"(original_id) WHERE is_active = true;

-- Unique document identity (for idempotent re-imports)
-- Enforced for active rows; document identity fields are mandatory.
CREATE UNIQUE INDEX idx_order_active_per_document_identity
ON "order"(document_issuer, document_type, document_number, document_date)
WHERE is_active = true;

-- GIN index for JSONB queries
CREATE INDEX idx_order_data ON "order" USING GIN (extracted_data);

-- Comments for documentation
COMMENT ON TABLE "order" IS 'Stores inbound vault order/invoice extractions from PDF documents with optional versioning';
COMMENT ON COLUMN "order".original_id IS 'Groups versions together (same semantics as extraction.original_id)';
COMMENT ON COLUMN "order".storage_path IS 'Relative path in bucket (extractions): "orders/{original_id}/{uuid}.pdf"';
COMMENT ON COLUMN "order".document_issuer IS 'Issuer/vendor identifier used as part of a unique document identity (document_issuer + document_type + document_number + document_date)';
COMMENT ON COLUMN "order".document_date IS 'Document identity date; if the PDF has no dedicated document date, derive this from order_date';
COMMENT ON COLUMN "order".shipping_date IS 'Estimated shipping date from the document (renamed from est_ship_date)';
COMMENT ON COLUMN "order".extracted_data IS 'JSONB containing canonical OrderExtractedData (see docs/domains/ORDER.md)';
COMMENT ON COLUMN "order".status IS 'Workflow status (order_status enum)';

-- 4) Order line items (structured positions)
-- 4) Order items (structured positions) with audit trail/versioning
CREATE TABLE order_item (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id UUID NOT NULL REFERENCES "order"(id) ON DELETE CASCADE,

    -- Link to original item (for history tracking)
    original_id UUID NOT NULL,

    -- User who created this version
    updated_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,

    -- Minimal canonical fields
    serial_number TEXT,
    item TEXT,
    description TEXT,
    quantity TEXT,
    item_price NUMERIC,
    total_price NUMERIC,

    -- Optional bullion-friendly fields
    metal bullion_metal NOT NULL DEFAULT 'unknown',
    -- TODO: Consider switching to a numeric grams column (e.g. weight_grams NUMERIC)
    -- and aligning the storage type with the existing `extraction.weight` / `extraction.weight_unit` fields.
    -- Keep as TEXT for now to stay consistent with current extraction persistence and normalization.
    weight TEXT,
    weight_unit bullion_weight_unit NOT NULL DEFAULT 'unknown',
    fineness TEXT,
    producer TEXT,
    form bullion_form NOT NULL DEFAULT 'unknown',

    raw JSONB NOT NULL DEFAULT '{}',
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_order_item_order_id ON order_item(order_id);
CREATE INDEX idx_order_item_original_id ON order_item(original_id);
CREATE INDEX idx_order_item_is_active ON order_item(is_active);
CREATE INDEX idx_order_item_item ON order_item(item);
CREATE INDEX idx_order_item_metal ON order_item(metal);
CREATE INDEX idx_order_item_form ON order_item(form);
CREATE UNIQUE INDEX idx_order_item_active_per_original
ON order_item(order_id, original_id)
WHERE is_active = true;

COMMENT ON TABLE order_item IS 'Structured order positions extracted from an order/invoice PDF with audit trail (versioned by original_id)';
COMMENT ON COLUMN order_item.raw IS 'Raw extracted row payload for audit/debug (optional)';
