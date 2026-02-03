# Domain: Order (Inbound Vault Deliveries)

This document defines the shared **domain model**, **workflow**, and **invariants** for inbound vault deliveries that are accompanied by an **Order Confirmation / Invoice / Delivery Note (PDF)**.

It is intentionally **cross-cutting**: both Server (FastAPI) and Studio (React/Vite) should rely on the same semantics.

Related domain docs:
- EXTRACTION.md — bullion bar extraction domain (image-based)

---

## Problem Statement

In a vault goods-receiving (German: *Wareneingang*) workflow, shipments of bullion bars arrive.
For each shipment there is typically a PDF document:
- Order confirmation
- Invoice
- Delivery note (*Lieferschein*)

The receiving workflow is:

1. Upload the PDF document.
2. Extract structured order data from it.
3. Return extraction result to the client.
4. Persist the extracted order data in a new database table (and store the PDF artifact).
5. Later, map inbound **bar extractions** (image-based `extraction` rows) to this order.
6. Validate that the received bars match the order.

A key nuance:
- The PDF order documents typically **do not contain bar serial numbers**.
- Serial numbers come from the **bar extraction** domain (`extraction`) when scanning each bar.

---

## Domain Concepts

### Order
Represents the *expected* content of a delivery/shipment.

An `Order` is derived from one primary document (PDF) and may be enriched over time by mapping scanned bars.

### Persistence, Snapshots, and “Bitemporal” Versioning

The database stores Orders and Order Items as **immutable snapshots**.
Every successful extraction run creates a **new snapshot row** (a new `order.id`), even when the PDF bytes are identical.

This design enables:
- a complete audit/history of extractions and corrections
- safe re-extraction without overwriting prior results
- a simple “current view” via `is_active=true`

#### Keys and meaning

Orders are versioned by two identifiers:

- `order.id`: unique ID of this specific snapshot/version.
- `order.original_id`: stable ID shared across all snapshots that represent the **same real-world document identity**.

Order Items follow the same pattern:

- `order_item.id`: unique ID of this specific line-item snapshot.
- `order_item.original_id`: stable ID for a logical item across versions (if/when we introduce item-level continuity).

#### Current vs. historical

- `order.is_active=true` marks the **current** snapshot for a given `original_id`.
- Older snapshots remain in the table with `is_active=false`.

Operationally, when a new extraction for the same identity is persisted:

1. The previously active `order` snapshot is marked inactive.
2. Previously active `order_item` rows for the same logical order are marked inactive.
3. A new `order` snapshot is inserted and becomes active.
4. A new set of `order_item` snapshots is inserted and becomes active.

Note: This is “bitemporal” in the sense that we retain a history of system-time snapshots (via `created_at`) and a clear current pointer (`is_active`).
We do not currently model explicit valid-time intervals like `valid_from/valid_to`.

#### Identity boundary (what constitutes the “same” order)

Two persisted snapshots belong to the same `original_id` if their **document identity** matches:

- `document_issuer`
- `document_type`
- `document_number`
- `document_date`

If any of these cannot be determined reliably, persistence must not create a snapshot (domain invariant).

#### PDF storage and re-extraction

The PDF artifact is stored by **content hash** and referenced by path:

- `order.storage_path = orders/by-hash/<sha256>.pdf`

Therefore:
- re-uploading the exact same PDF bytes produces the **same** `storage_path`
- re-extracting the same PDF still creates a **new** order snapshot (`order.id` differs)

This keeps storage deduplicated while preserving an extraction audit trail.

#### Actor attribution (`updated_by`)

Snapshots can be attributed to the actor that triggered them:

- `order.updated_by`: user/service identifier that initiated the snapshot
- `order_item.updated_by`: same attribution for inserted item snapshots

When `updated_by` is `null`, the system could not attribute the run (treated as “System/Unknown” in UIs).

### Order Document
A PDF artifact (invoice / delivery note / order confirmation) used to derive the order.

The system stores:
- raw file bytes (artifact)
- extracted structured fields (normalized)
- extraction metadata (strategy, confidence, processing time, errors)

### Order Line Item
Represents one expected product position from the document.

Typical attributes:
- product identifier (if present)
- description
- quantity
- unit (if present)
- weight / fineness / metal (if present)

### Bar Extraction Mapping
A relationship between an `Order` and one or more `extraction` rows (bullion bar scans).

This mapping enables:
- matching received bars to ordered items
- detecting missing / extra bars
- detecting mismatched attributes (e.g., wrong metal, wrong weight)

---

## Canonical Order Schema (Phase 1)

Phase 1 requires a **single canonical schema** that the server returns consistently, regardless of which PDF issuer/layout produced it.

Principles:
- The schema must be stable (adding optional fields is OK; renaming/removing is breaking).
- The schema must separate **raw extracted values** from **normalized values** where ambiguity exists.
- The schema must represent what the document can reasonably provide.
  - Bar serial numbers are not expected on order documents.

---

## Strategy Mechanism (Order)

Order extraction is strategy-based to keep the manual pipeline clean today and enable future extensions without changing the response schema.

Supported strategies:
- `manual` — heuristic, text-based parsing (default)
- `cloud` — AI-backed extraction strategy

Both strategies:
- produce the same canonical order schema
- participate in the same post-processing and finalization pipeline
- are subject to the same domain-level validity rules

---

## Document Identifier Whitelist

Issuer-specific document identification rules (issuer match needles, optional doc-type weights,
and optional document number/date regexes) are configured via:
- `config/order/document_identifier_whitelist.json`

This keeps issuer routing maintainable without pushing every new issuer into Python code.

## Trace Model (Tree)

Order extraction emits a **hierarchical trace tree** (not a flat list of steps). The goal is to make “brackets/spans” explicit (e.g. `strategy.extract_from_text` as a *Klammer* around everything the chosen strategy does).

The trace is used for:
- Server logs (pretty-printed, indented)
- Studio debug UI (tree view + KPI derivation)

### Node Types

The trace is a JSON tree rooted at a **span**:

- **Span** (`type: "span"`): timed block with `start_ms`, `end_ms`, `duration_ms`, `status` and optional `attrs`, `error`, `artifacts`, `children`.
- **Event** (`type: "event"`): point-in-time decision/annotation with `at_ms`, optional `attrs`.

Large debug payloads are stored as **artifacts** (attached to the *current span*):

- **Artifact**: `{ key, content_type, value, size, truncated }`

Artifacts are expected to be **sanitized** and may be truncated.

### Canonical Structure

The canonical root is:

- `order.process` (span)

Canonical spans/events (current baseline):

- `input.textify` (span)
  - `decision.textify` (event): records which textification mode was used (currently default `pdf_text`)
- `strategy.pipeline` (span)
  - `decision.strategy_choice` (event): records why a strategy was chosen (currently request param)
  - `raw_signals.extract` (span): strategy-independent raw signals extraction (lines/KV/tables)
    - Trace attributes (non-exhaustive):
      - `kv_keys_top`: first N unique `key_normalized` values (for quick triage)
      - `table_names`: extracted raw table names
      - `contact_emails`: number of extracted email domains
      - `contact_email_domains_top`: top email domains (PII-safe; no full addresses)
      - `contact_websites`: number of extracted website hosts
      - `contact_websites_top`: top website hosts
  - `detect.initial` (span): strategy-independent initial document detection (issuer/type candidates)
  - `strategy.extract_from_text` (span): **the strategy bracket**

Within the chosen strategy (inside `strategy.extract_from_text`), common spans include:

- `preprocessing.<step>` (span)
- `detect.identity` (span)
- `markers.build_marker_text` (span) or `markers.built` (event)
  - artifact `marker.text` (`text/plain`, truncated)
- `cloud.ai_extract` (span)
  - `cloud.ai_extract.attempt` (span) with `attrs.attempt = 1..N`
    - artifact `llm.request` (JSON)
    - artifact `llm.response` (JSON, may be truncated)
- `postprocessing.<step>` (span)
- `persistence.order.persist_to_supabase` (span): persistence boundary (outside strategy)

Postprocessing spans may contain additional debug/provenance information:

- `summary` (string): a short human-readable statement of what changed (e.g. `set parties.shipping_to=...`).
- artifact `mapping.patch` (`application/json`): a mapping overlay that marks changed target fields with
  `{ "source": "postprocessing.<step>" }`. These patches are merged into `meta.field_mapping`.

Finalization/validation:

- `finalize.finalize_order_extraction` (span)
- `validate.OrderExtractedData.model_validate` (span)

### Attempts vs. Retries

The trace models multiple calls to an LLM as **attempts** (not “retries”). Each attempt is represented as a child span:

- `cloud.ai_extract.attempt` with an integer `attempt` attribute

This keeps the model flexible for future behavior (e.g. different prompts/models per attempt).

Note: a semantic fallback may trigger a second pass that re-runs:
- `input.textify` (vision marker-text, `attempt=2`)
- `raw_signals.extract` (`attempt=2`)
- `detect.initial` (`attempt=2`)
- `strategy.extract_from_text` (`attempt=2`)

### Persistence Boundary

Persistence is intentionally **outside** the strategy:

- The strategy is responsible for producing the canonical extraction result (and emitting its trace spans).
- Persisting the PDF / extracted order to Supabase happens at the API layer.

This boundary prevents “side effects inside strategies” and keeps future multi-strategy pipelines composable.

---

## Field Mapping / Provenance (meta.field_mapping)

The extraction response meta contains a `field_mapping` section which mirrors the **target** `structured_data` shape.

For every leaf field in `structured_data`, the mapping contains a small provenance marker object, e.g.:

- `{ "source": "cloud.ai" }`
- `{ "source": "detect.identity", "field": "detect.identity.document_date" }`

This makes it easy to see *where each output field came from* without scanning logs.

Notes:
- The mapping is intended for debug/audit only.
- It MUST NOT contain secrets.
- Some sources may be coarse today (e.g. default `cloud.ai` / `parse.default_order`), and will become more granular over time.
- Provenance overlays can come from multiple layers (e.g. strategy-level hints and postprocessing `mapping.patch`).

---

## Manual Strategy (Heuristic Parsing)

The manual strategy is the default extraction mechanism.

Characteristics:
- relies on layout-aware PDF text extraction
- uses deterministic heuristics to detect key/value pairs and tables
- prefers conservative extraction over guessing
- produces stable and predictable results for known layouts

Raw signals notes:
- Table extraction supports multiline rows: if a table has a `Description` column and a subsequent line
  contains only a single text cell, it is treated as a continuation of the previous row's description.
- Tables stop at total markers (e.g. `Total`, `Sub Total`) to avoid swallowing summary sections.
- The raw KV may include identity candidates from footer patterns (e.g. `document_type_candidate`,
  `document_number_candidate`) when a document contains lines like `Contract Note | Reference: ...`.

The manual strategy is expected to fail explicitly if required invariants
(e.g. document identity or order items) cannot be satisfied.

---

## Cloud Strategy (AI-backed Order Extraction)

In addition to the manual/heuristic parsing strategy, the Order domain supports
an AI-backed **cloud extraction strategy**.

The cloud strategy is intended to:
- recover structured order data when manual heuristics are insufficient
- handle complex, highly variable, or scanned PDF layouts
- return the same canonical `OrderExtractedData` schema as the manual strategy

### Contract-based behavior

The cloud strategy is governed by an explicit operational contract:

- `config/order/ORDER_EXTRACTION_AI_CONTRACT.md`

This contract defines:
- extraction invariants
- raw vs. structured data guarantees
- bullion item semantics
- confidence and reconciliation readiness rules

The cloud strategy MUST comply with this contract.
Prompts and model-specific logic are considered implementation details.

### Strategy parity

If the cloud strategy cannot satisfy required invariants
(e.g. missing document identity or missing order items),
the extraction MUST fail explicitly and must not persist an invalid order.

---

## Invariants

### Order Identity
- An Order must have a stable document identity.
- Missing issuer, document number, or date renders the extraction invalid.

### No Serial Numbers in Documents
- Order document extraction must not assume serial numbers exist.
- Serial numbers are introduced only via bar extraction and mapping.

### Explicit Matching
- A bar is considered part of an order only after explicit mapping.
- No implicit matching based solely on attributes.

---

## Notes

This document intentionally avoids describing extraction heuristics or AI behavior in detail.
Such rules are defined in the respective strategy implementations and, for the cloud strategy,
in the explicit extraction contract.
