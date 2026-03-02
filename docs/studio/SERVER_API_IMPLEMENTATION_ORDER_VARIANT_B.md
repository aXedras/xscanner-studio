# Server API Implementation Order — Variant B (Frontend Expectations)

This document is the implementation handoff for server teams.
It defines exactly which endpoint to build first, and the request/response shape the Studio frontend expects.

## Goal

Migrate Studio API-by-API with contract stability, no hidden defaults, and strict compatibility with frontend adapters.

## Migration Status Tracker (2026-03-02)

Legend:

- `FE Ready`: frontend adapter and tests are available in Studio.
- `Server Pending`: endpoint contract is defined but server implementation is still open.
- `Next`: first endpoint to implement next.

| API | Endpoint | FE status | Server status | Priority |
|---|---|---|---|---|
| #1 | `GET /api/v1/orders` | FE Ready | Server Pending | **Next** |
| #2 | `GET /api/v1/orders/status-counts` | FE Ready | Server Pending | High |
| #3 | `GET /api/v1/orders/by-original/{originalId}/active` | FE Ready | Server Pending | High |
| #4 | `GET /api/v1/orders/by-original/{originalId}/history` | FE Ready | Server Pending | High |
| #5 | `GET /api/v1/extractions` | FE Ready | Server Pending | High |
| #6 | `GET /api/v1/extractions/status-counts` | FE Ready | Server Pending | High |
| #7 | `GET /api/v1/extractions/by-original/{originalId}/active` | FE Ready | Server Pending | High |
| #8 | `GET /api/v1/extractions/by-original/{originalId}/history` | FE Ready | Server Pending | High |
| #9 | `GET /api/v1/bil/registrations` | FE Ready | Server Pending | High |
| #10 | `POST /api/v1/bil/registrations:batch` | FE Ready | Server Pending | High |
| #11 | `POST /api/v1/extractions/{originalId}/validate` | FE Ready | Server Pending | Medium |
| #12 | `POST /api/v1/extractions/{originalId}/reject` | FE Ready | Server Pending | Medium |
| #13 | `POST /api/v1/extractions/{originalId}/corrections` | FE Ready | Server Pending | Medium |
| #14 | `POST /api/v1/auth/sign-in` | FE Ready | Server Pending | Medium |
| #15 | `POST /api/v1/auth/sign-up` | FE Ready | Server Pending | Medium |
| #16 | `POST /api/v1/auth/sign-out` | FE Ready | Server Pending | Medium |
| #17 | `GET /api/v1/auth/session` | FE Ready | Server Pending | Medium |

## Global Contract Rules (mandatory)

- Base path: `/api/v1`
- Content type: `application/json`
- Non-2xx error envelope:

```json
{
  "error": {
    "code": "SOME_STABLE_CODE",
    "message": "Human readable message",
    "details": null,
    "request_id": "req_123"
  }
}
```

- Paged success envelope:

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "page_size": 10
}
```

- Query field naming must be `snake_case` where specified below.

## API #1 — Build First

## `GET /api/v1/orders`

This is the first endpoint to implement and release.
Frontend caller: `orderService.listActivePaged()` via `HttpOrderReadService`.

### Query parameters

- `page` (required, integer >= 1)
- `page_size` (required, integer >= 1)
- `sort_field` (optional, e.g. `created_at`)
- `sort_direction` (optional, `asc|desc`)
- `search` (optional, trimmed string)
- `created_at_from` (optional, ISO date/time)
- `created_at_to` (optional, ISO date/time)
- `status` (optional, repeatable; e.g. `status=pending&status=validated`)

### Success response (`200`)

```json
{
  "items": [
    {
      "id": "order-1",
      "original_id": "orig-1",
      "status": "pending"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 10
}
```

### Error responses

- `400` invalid query/filter/sort/pagination
- `401/403` when auth is required and invalid
- `500` internal failures

All errors must use the global error envelope.

### Contract tests required before handoff

- Accepts all listed query fields.
- Applies stable deterministic sorting.
- Pagination metadata is always present and valid.
- Invalid query values return `400` with stable `error.code`.

## API #2

## `GET /api/v1/orders/status-counts`

Frontend caller: `orderService.getActiveStatusCounts()`.

### Query parameters

- `search` (optional)
- `created_at_from` (optional)
- `created_at_to` (optional)

### Success response (`200`)

Must match frontend `OrderStatusCounts` shape (stable keys, include zero values).

```json
{
  "pending": 0,
  "validated": 0,
  "rejected": 0,
  "error": 0,
  "total": 0
}
```

## API #3

## `GET /api/v1/orders/by-original/{originalId}/active`

Frontend caller: `orderService.findActiveByOriginalId()`.

### Path parameter

- `originalId` (required)

### Success response (`200`)

Single active order snapshot object.

### Not found behavior

- Current frontend adapter maps `404` to `null`.
- Keep this behavior stable and documented.

## API #4

## `GET /api/v1/orders/by-original/{originalId}/history`

Frontend caller: `orderService.findHistoryByOriginalId()`.

### Success response (`200`)

Array of order snapshots in stable order (recommended: newest first).

### Not found behavior

- Current frontend adapter maps `404` to `[]`.
- Keep this behavior stable and documented.

## API #5

## `GET /api/v1/extractions`

Frontend caller: `extractionService.listActivePaged()` via `HttpExtractionReadService`.

### Query parameters

Same semantics as orders list:

- `page`, `page_size`
- `sort_field`, `sort_direction`
- `search`
- `created_at_from`, `created_at_to`
- repeatable `status`

### Success response (`200`)

Same paged envelope with extraction item DTOs.

## API #6

## `GET /api/v1/extractions/status-counts`

Frontend caller: `extractionService.getActiveStatusCounts()`.

### Query parameters

- `search`, `created_at_from`, `created_at_to`

### Success response (`200`)

Stable extraction status counts with all expected keys present.

## API #7

## `GET /api/v1/extractions/by-original/{originalId}/active`

Frontend caller: `extractionService.getActiveByOriginalId()`.

- `404` is currently mapped to `null` by frontend adapter.

## API #8

## `GET /api/v1/extractions/by-original/{originalId}/history`

Frontend caller: `extractionService.getHistoryByOriginalId()`.

- `404` is currently mapped to `[]` by frontend adapter.

## API #9

## `GET /api/v1/bil/registrations`

Frontend caller: `bilService.listRegistrationsByExtractionId()`.

### Query parameters

- `extraction_id` (required)

### Success response (`200`)

Array of BIL registration rows.

## API #10

## `POST /api/v1/bil/registrations:batch`

Frontend caller: `bilService.listRegistrationsByExtractionIds()`.

### Request body

```json
{
  "extraction_ids": ["ext-1", "ext-2"]
}
```

### Success response (`200`)

Array of BIL registration rows.

## API #11

## `POST /api/v1/extractions/{originalId}/validate`

Frontend caller: `extractionService.validateActive()` via `HttpExtractionMutationService`.

### Request body

```json
{
  "updatedBy": "user-1"
}
```

### Success response (`200`)

Updated/created extraction snapshot row.

## API #12

## `POST /api/v1/extractions/{originalId}/reject`

Frontend caller: `extractionService.rejectActive()`.

### Request body

```json
{
  "updatedBy": "user-1"
}
```

### Success response (`200`)

Updated/created extraction snapshot row.

## API #13

## `POST /api/v1/extractions/{originalId}/corrections`

Frontend caller: `extractionService.createCorrectionVersion()`.

### Request body

```json
{
  "corrected": {
    "serial_number": null,
    "metal": null,
    "weight": null,
    "weight_unit": null,
    "fineness": null,
    "producer": null
  },
  "updatedBy": "user-1"
}
```

### Success response (`200`)

Created corrected extraction snapshot row.

## API #14

## `POST /api/v1/auth/sign-in`

Frontend caller: `authService.signIn()` via `HttpAuthRepository`.

### Request body

```json
{
  "email": "user@example.com",
  "password": "secret"
}
```

### Success response (`200`)

```json
{
  "hasSession": true
}
```

## API #15

## `POST /api/v1/auth/sign-up`

Frontend caller: `authService.signUp()`.

### Request body

```json
{
  "email": "user@example.com",
  "password": "secret",
  "displayName": "User One"
}
```

### Success response (`200`)

```json
{
  "hasSession": false
}
```

## API #16

## `POST /api/v1/auth/sign-out`

Frontend caller: `authService.signOut()`.

### Request body

```json
{}
```

### Success response

- Preferred: `204 No Content`
- Alternative accepted by current frontend client: `200` with empty JSON object

## API #17

## `GET /api/v1/auth/session`

Frontend caller: `authService.getSession()` and app bootstrap.

### Success response (`200`)

```json
{
  "session": {
    "id": "user-1",
    "email": "user@example.com",
    "user_metadata": {
      "display_name": "User One"
    }
  }
}
```

or

```json
{
  "session": null
}
```

## Delivery rule per endpoint

Server handoff is only complete when all are true:

1. Endpoint implemented under `/api/v1`.
2. OpenAPI updated.
3. Contract tests green for success and error cases.
4. Error codes stable and documented.
5. Frontend adapter integration test green against mocked contract.

## Recommended execution sequence

1. API #1-#4 (Orders read)
2. API #5-#10 (Extractions read + BIL read)
3. API #11-#13 (Extractions mutations)
4. API #14-#17 (Auth/session)

Do not start the next endpoint family before the current family has contract tests and stable behavior.