# Contract Test Checklist — Variant B Server Handoff

Concrete, implementation-ready contract test checklist for the server repository.

Use this document together with:

- `API_CONTRACT_BACKLOG_VARIANT_B.md`
- `SERVER_REPO_PLAYBOOK_VARIANT_B.md`
- `openapi/auth-v1.yaml`

## Global Contract Rules

- [ ] Endpoint is mounted under `/api/v1`.
- [ ] Non-2xx responses use the shared error envelope (`error.code`, `error.message`, `error.request_id`).
- [ ] Unknown query/body fields are either validated or explicitly ignored (documented behavior).
- [ ] Input validation errors return `400` with stable `error.code`.
- [ ] Authentication/authorization failures return `401/403` with stable `error.code`.

## Auth & Session

## POST `/api/v1/auth/sign-in`

- [ ] Returns `200` with `{ hasSession: true|false }` for valid payload.
- [ ] Returns `400` for malformed payload (missing email/password, invalid email format).
- [ ] Returns `401` for invalid credentials.
- [ ] Trims email input before authentication.

## POST `/api/v1/auth/sign-up`

- [ ] Returns `200` with `{ hasSession: true|false }` for valid payload.
- [ ] Returns `400` for missing/invalid fields (`email`, `password`, `displayName`).
- [ ] Returns `409` for already-existing user.
- [ ] Persists/propagates `displayName` consistently.

## POST `/api/v1/auth/sign-out`

- [ ] Returns `204` on successful sign-out.
- [ ] Returns `401` for missing/invalid session token when auth is required.

## GET `/api/v1/auth/session`

- [ ] Returns `200` with `{ session: null }` when no active session exists.
- [ ] Returns `200` with `{ session: { id, email, user_metadata.display_name? } }` when authenticated.
- [ ] Session payload fields match frontend `AuthSessionUser` model.

## Orders Read

## GET `/api/v1/orders`

- [ ] Supports `page`, `page_size`, `sort_field`, `sort_direction`, `search`, `status[]`.
- [ ] Returns pagination envelope with deterministic sort order.
- [ ] Rejects invalid pagination/sort params with `400`.

## GET `/api/v1/orders/status-counts`

- [ ] Applies same filter semantics as `/orders` for `search` and date filters.
- [ ] Returns stable shape for all status counters (including zeros).

## GET `/api/v1/orders/by-original/{originalId}/active`

- [ ] Returns active snapshot for existing `originalId`.
- [ ] Returns `404` for unknown `originalId`.

## GET `/api/v1/orders/by-original/{originalId}/history`

- [ ] Returns full version history in expected order.
- [ ] Returns `404` or empty list according to final contract (must be documented and consistent).

## Extractions Read

## GET `/api/v1/extractions`

- [ ] Supports `page`, `page_size`, `sort_field`, `sort_direction`, `search`, `status[]`, date range.
- [ ] Returns pagination envelope with deterministic sort order.
- [ ] Rejects invalid pagination/sort/date params with `400`.

## GET `/api/v1/extractions/status-counts`

- [ ] Uses same filtering semantics as `/extractions`.
- [ ] Returns all expected status counters with stable keys.

## GET `/api/v1/extractions/by-original/{originalId}/active`

- [ ] Returns active snapshot for existing `originalId`.
- [ ] Returns `404` for unknown `originalId`.

## GET `/api/v1/extractions/by-original/{originalId}/history`

- [ ] Returns full version history for `originalId`.
- [ ] Returns `404` or empty list according to final contract (must be documented and consistent).

## BIL Read

## GET `/api/v1/bil/registrations`

- [ ] Requires `extraction_id` query param.
- [ ] Returns list for existing extraction.
- [ ] Returns empty list for no matches (or `404` if chosen; must stay consistent).

## POST `/api/v1/bil/registrations:batch`

- [ ] Accepts `extraction_ids[]` body.
- [ ] Trims/normalizes IDs or rejects invalid IDs (documented behavior).
- [ ] Returns combined list with deterministic ordering guarantees (if any).

## Extractions Mutation

## POST `/api/v1/extractions/{originalId}/validate`

- [ ] Requires `updatedBy` and validates actor identity/permissions.
- [ ] Creates expected new active version and transitions previous version correctly.
- [ ] Triggers/records BIL registration behavior as contractually defined.

## POST `/api/v1/extractions/{originalId}/reject`

- [ ] Requires `updatedBy` and validates actor identity/permissions.
- [ ] Creates expected rejected active version.

## POST `/api/v1/extractions/{originalId}/corrections`

- [ ] Requires `updatedBy` and `corrected` payload.
- [ ] Rejects invalid field values with `400`.
- [ ] Creates a new corrected version and preserves audit history.

## Delivery Evidence Required From Server Repo

- [ ] OpenAPI spec updated for implemented endpoints.
- [ ] Contract test files/links provided per endpoint family.
- [ ] Example success and error payloads provided.
- [ ] Changelog entry documents behavior decisions (e.g., 404 vs empty list).
