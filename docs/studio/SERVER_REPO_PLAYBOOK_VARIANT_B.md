# Server Repo Playbook — Variant B Migration

Practical checklist for the server repository while Studio migrates to API-only persistence access.

Primary handoff references:

- `API_CONTRACT_BACKLOG_VARIANT_B.md`
- `CONTRACT_TEST_CHECKLIST_VARIANT_B.md`
- `openapi/auth-v1.yaml`

## Operating Mode

- Keep existing server-side Studio/client code temporarily if needed.
- Build new API contracts incrementally.
- Do not block Studio migration on full backend cleanup.

## Phase A — Foundations

- [ ] Add API version namespace (`/api/v1`) and shared error envelope.
- [ ] Add request-id propagation middleware.
- [ ] Add contract test harness for endpoint request/response validation.

## Phase B — Orders read-only (first implementation target)

- [ ] Implement `GET /api/v1/orders`
- [ ] Implement `GET /api/v1/orders/status-counts`
- [ ] Implement `GET /api/v1/orders/by-original/{originalId}/active`
- [ ] Implement `GET /api/v1/orders/by-original/{originalId}/history`
- [ ] Add filters + sort + pagination parity with Studio query semantics.
- [ ] Add contract tests and integration tests.

## Phase C — Extractions read-only + BIL reads

- [ ] Implement `GET /api/v1/extractions`
- [ ] Implement `GET /api/v1/extractions/status-counts`
- [ ] Implement `GET /api/v1/extractions/by-original/{originalId}/active`
- [ ] Implement `GET /api/v1/extractions/by-original/{originalId}/history`
- [ ] Implement `GET /api/v1/bil/registrations`
- [ ] Implement `POST /api/v1/bil/registrations:batch`

## Phase D — Mutations and attribution

- [ ] Implement `POST /api/v1/extractions/{originalId}/validate`
- [ ] Implement `POST /api/v1/extractions/{originalId}/reject`
- [ ] Implement `POST /api/v1/extractions/{originalId}/corrections`
- [ ] Implement `PATCH /api/v1/orders/{orderId}`
- [ ] Implement item mutation endpoints (`create/update/delete`)
- [ ] Implement snapshot attribution endpoints for orders/items.

## Phase E — Auth/session and storage

- [ ] Implement `/api/v1/auth/sign-in`, `/sign-up`, `/sign-out`, `/session`.
- [ ] Implement `/api/v1/storage/preview-url` signed-url endpoint.

## Quality Requirements (server repo)

- [ ] Lint + type checks + tests must pass before each merge.
- [ ] Contract tests mandatory for every new endpoint.
- [ ] Error codes documented and stable.
- [ ] Backward compatibility maintained for existing Studio calls during transition.
- [ ] `CONTRACT_TEST_CHECKLIST_VARIANT_B.md` checklist is updated per delivered slice.

## Handoff to Studio Repo per Slice

For each delivered slice, provide to Studio team:

1. Endpoint list and example payloads.
2. Error code catalog.
3. Query parameter semantics.
4. Contract test artifacts (or schema references).
5. Known edge cases and rate/timeout expectations.
