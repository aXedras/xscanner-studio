# ORDER_EXTRACTION_AI_CONTRACT (v1.0)

Status: Stable
Scope: LLM-backed Order Extraction Strategy ("cloud")
Related:
- docs/domains/ORDER.md
- docs/ORDER_EXTRACTION_WORKFLOW.md

---

## 1. Purpose

This document defines the **explicit contract** between the Order domain and an AI-based extraction strategy.

It specifies:
- what the AI is allowed and required to extract
- how extracted data must be structured
- which invariants must never be violated
- how confidence and readiness are determined

This document is **normative** for AI extraction behavior.
Prompts are considered **implementations** of this contract.

---

## 2. Core Principles (Hard Rules)

1. **No invention**
   The AI MUST only emit data that can be justified by explicit evidence in the document.

2. **Raw + Structured always together**
   Every extraction result MUST contain both:
   - raw signals (`raw_kv`, `raw_tables`)
   - mapped canonical data (`structured_data`)

3. **Missing beats wrong**
   If a value cannot be determined with confidence, it MUST be returned as an empty value, never guessed.

4. **Order Items are critical**
   An extraction without usable `order_items` is considered invalid.

5. **Documents do not contain bar serial numbers by default**
   Serial numbers are introduced later via bar extraction and mapping.

---

## 3. Output Envelope

The AI extraction result MUST conform to the following envelope:

- `meta`
- `raw`
- `structured_data`

No additional top-level fields are permitted.

---

## 4. Raw Data Contract

### 4.1 raw_kv

- Represents best-effort key/value pairs derived from the document text.
- Keys MUST be normalized to `snake_case` in `key_normalized`.
- Values MUST reflect the document text as closely as possible.
- Derived routing/identity signals (issuer, type, number, date, receiver) MUST appear first.

### 4.2 raw_tables

- Tables MUST preserve header order and row order.
- When an order items table is detected, it MUST be included verbatim.
- Table naming is descriptive but not semantic (e.g. `terms`, `order_items`).

Raw data exists for **auditability and repair**, not as a business interface.

---

## 5. Document Identity (Critical)

The following fields form the **document identity**:

- `document.document_issuer`
- `document.document_type`
- `document.document_number`
- `document.document_date`

Rules:
- All four fields are REQUIRED.
- If any field cannot be determined, the extraction is INVALID.
- `document_date` MUST be an ISO date (`YYYY-MM-DD`).

Confidence for these fields MUST be tracked individually.

---

## 6. Order Items (Critical)

`order_items` represent the expected contents of the delivery and are the foundation for reconciliation.

### 6.1 Minimum Required Fields

Each item MUST contain at least:
- `item` OR `description`
- `quantity`

### 6.2 Bullion Semantics (Best-Effort, High Importance)

The following fields MUST be extracted conservatively from `description` and/or `item`:

- `metal`
- `producer`
- `weight`
- `weight_unit`
- `form`
- `fineness`

Rules:
- `metal` MUST be derived from explicit textual matches (EN/DE).
- `producer` MUST match a known whitelist entry.
- `weight` MUST include both numeric value and unit.
- `fineness` MUST be an empty string ("") if not explicitly present.
- `form` MUST only be set if explicitly derivable.

### 6.3 Serial Number Policy

- Order documents are NOT expected to contain serial numbers by default.
- A flag `serial_number_expected` controls criticality.
- If `serial_number_expected = true` and no serial number is found:
  - the extraction is NOT reconciliation-ready.

---

## 7. Confidence Model

Confidence is not cosmetic; it drives workflow decisions.

### 7.1 Primary Confidence Axes

1. **Document Identifiers Confidence**
2. **Order Items Confidence** (dominant)

### 7.2 Field-Level Confidence

Tracked explicitly for:
- document_issuer
- document_type
- document_number
- document_date

Scale:
- `1.0` – unambiguous, labeled, deterministic
- `0.8` – clear but inferred
- `0.5` – ambiguous candidate
- `0.0` – missing

### 7.3 Order Items Confidence

Derived from:
- presence of a detected items table
- presence of quantity and prices
- numeric plausibility checks
- absence of structural ambiguity

---

## 8. Reconciliation Readiness

An extraction is considered **reconciliation-ready** if and only if:

- document identity is complete
- `order_items` is non-empty
- order items confidence ≥ defined threshold
- no critical warnings are present
- serial number expectations (if any) are satisfied

This decision MUST be made explicit via a boolean flag and reason.

---

## 9. Explicit Non-Goals

The AI extraction strategy MUST NOT:
- invent missing values
- normalize prices beyond string preservation
- assume serial numbers exist
- implicitly match bars to orders
- hide missing required identity fields via defaults

---

## 10. Versioning

This contract is versioned independently of prompts and code.

- Draft versions MAY evolve rapidly.
- `v1.0` marks semantic stability for production reliance.

Prompts SHOULD reference the contract version they implement.

---

## 11. Operational Data (Shared Whitelists)

This contract relies on shared bullion-domain whitelists stored in:
- `config/whitelists/producers.json`
- `config/whitelists/metals.json`
- `config/whitelists/forms.json`
- `config/whitelists/weight_units.json`
- `config/whitelists/serial_number_patterns.json`

Rules:
- `producer` MUST match the producer whitelist (case-insensitive, alias-aware).
- `metal`, `form`, and `weight_unit` MUST match their respective whitelists.
- Whitelists are operational data and may evolve without changing domain invariants.
