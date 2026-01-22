# Domain: Extraction (Server + Studio)

This document defines the shared **domain model** and **invariants** for extraction runs.

It is intentionally **cross-cutting**: both Server (FastAPI) and Studio (React/Vite) depend on these semantics.

For persistence mechanics (Supabase, migrations, generated DB types), see [../PERSISTENCE.md](../PERSISTENCE.md).

## Overview

An *extraction* represents the result of analyzing an uploaded image and producing structured data.

Key properties:
- Stored in Postgres as rows in the `extraction` table.
- Image bytes stored in Supabase Storage, referenced by `storage_path`.
- The domain supports **auditable corrections** by creating new versions.

## Versioning Model (Audit Trail)

The `extraction` table is versioned at the application level:

- Each logical extraction has a stable **group id**: `original_id`.
- Each version is a distinct row with its own `id`.
- Exactly one row per `original_id` is considered the current version: `is_active = true`.
- `created_at` represents **when this version row was created**.
- `updated_by` represents **who created this version row** (not “last updated”).

### Why there is no `updated_at`

Because corrections are modeled by inserting a new version row, `updated_at` would be misleading. The “change time” is already captured by the new version’s `created_at`.

## Correction Workflow

When a user corrects fields in Studio:

1. Load the current active row for a given `original_id`.
2. Insert a **new row** with:
   - same `original_id`
   - corrected field values
   - `updated_by = <current user id>`
   - `is_active = true`
3. Mark the previous row as `is_active = false`.

This produces a full audit trail that Studio can render as “what changed when by whom”.

## Status Semantics

The database enforces allowed status values via a Postgres enum (`extraction_status`).

Current rule:
- `status = pending` when `error` is null
- `status = error` when `error` is set

Additional domain statuses (e.g. validation/correction outcomes) are applied by Studio as part of QA flows.

## Storage Semantics (Images)

Extraction images are stored in Supabase Storage:

- Bucket: `extractions` (default)
- Path key: stored in DB as `storage_path`

Studio typically uses signed URLs for preview; if that fails, it can fall back to an authenticated download and render a blob URL.

## Server Responsibilities

- Accept uploads via API endpoints.
- Run extraction (real or mock).
- Persist each run to Supabase when persistence is configured.
- If Supabase is configured but unreachable, the API returns a structured HTTP 500 response (see API docs).

Related implementation:
- `src/xscanner/server/persistence.py`
- `src/xscanner/server/supabase_rest.py`

## Studio Responsibilities

- Treat the active row (`is_active = true`) as the current state.
- Create correction versions (new rows) instead of mutating previous versions.
- Render history per `original_id` for auditability.

Related implementation typically lives under:
- `studio/src/services/core/extraction/*`

## References

- Persistence mechanics: [../PERSISTENCE.md](../PERSISTENCE.md)
- API semantics: [../API_DOCUMENTATION.md](../API_DOCUMENTATION.md)
