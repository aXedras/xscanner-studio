# API Contract Backlog — Variant B (Frontend via Server API only)

Contract-first backlog for migrating Studio from frontend Supabase persistence to server-owned persistence.

Companion implementation docs:

- `CONTRACT_TEST_CHECKLIST_VARIANT_B.md`
- `openapi/auth-v1.yaml`

## Scope

- Source: current frontend service/repository interfaces.
- Target: server endpoints consumed by Studio HTTP clients.
- Goal: remove direct frontend persistence access incrementally.

## API Conventions

## Base path

- Proposed: `/api/v1`

## Error envelope (uniform)

All non-2xx responses should return:

```json
{
  "error": {
    "code": "ORDER_NOT_FOUND",
    "message": "Order not found",
    "details": null,
    "request_id": "req_..."
  }
}
```

## Pagination envelope

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "page_size": 10
}
```

## Migration Priority

1. Read-only flows (orders/extractions list + detail)
2. Mutations (validate/reject/corrections + order/item updates)
3. Auth/session
4. Storage preview/signing

## Contract Mapping — Auth

| Frontend source | Target endpoint | Method | Notes |
|---|---|---|---|
| `IAuthRepository.signInWithPassword` | `/api/v1/auth/sign-in` | `POST` | Body: `email`, `password`; response: `hasSession` |
| `IAuthRepository.signUpWithPassword` | `/api/v1/auth/sign-up` | `POST` | Body: `email`, `password`, `displayName`; response: `hasSession` |
| `IAuthRepository.signOut` | `/api/v1/auth/sign-out` | `POST` | Stateless sign-out contract |
| `App session bootstrap` | `/api/v1/auth/session` | `GET` | Replaces frontend direct session reads |

## Contract Mapping — Extractions

| Frontend source | Target endpoint | Method | Notes |
|---|---|---|---|
| `IExtractionRepository.findActivePaged` | `/api/v1/extractions` | `GET` | Query: page/page_size/sort/search/date/statuses |
| `IExtractionRepository.getActiveStatusCounts` | `/api/v1/extractions/status-counts` | `GET` | Query filters aligned with list filters |
| `IExtractionRepository.findActiveByOriginalId` | `/api/v1/extractions/by-original/{originalId}/active` | `GET` | Returns active snapshot or null |
| `IExtractionRepository.findHistoryByOriginalId` | `/api/v1/extractions/by-original/{originalId}/history` | `GET` | Descending by creation |
| `IExtractionService.validateActive` | `/api/v1/extractions/{originalId}/validate` | `POST` | Body: `updatedBy`; server performs BIL registration + status update |
| `IExtractionService.rejectActive` | `/api/v1/extractions/{originalId}/reject` | `POST` | Body: `updatedBy` |
| `IExtractionRepository.createCorrectionVersion` | `/api/v1/extractions/{originalId}/corrections` | `POST` | Body: corrected fields + `updatedBy` |
| `IBilRegistrationRepository.findByExtractionId` | `/api/v1/bil/registrations` | `GET` | Query: `extraction_id` |
| `IBilRegistrationRepository.findByExtractionIds` | `/api/v1/bil/registrations:batch` | `POST` | Body: `extraction_ids[]` |

## Contract Mapping — Orders

| Frontend source | Target endpoint | Method | Notes |
|---|---|---|---|
| `IOrderRepository.findActivePaged` | `/api/v1/orders` | `GET` | Query: page/page_size/sort/search/date/statuses |
| `IOrderRepository.getActiveStatusCounts` | `/api/v1/orders/status-counts` | `GET` | Query filters aligned with list filters |
| `IOrderRepository.findById` | `/api/v1/orders/{orderId}` | `GET` | Used by `resolveOriginalIdByOrderId` |
| `IOrderRepository.findActiveByOriginalId` | `/api/v1/orders/by-original/{originalId}/active` | `GET` | Active snapshot |
| `IOrderRepository.findHistoryByOriginalId` | `/api/v1/orders/by-original/{originalId}/history` | `GET` | Version history |
| `IOrderRepository.update` | `/api/v1/orders/{orderId}` | `PATCH` | Partial update |
| `IOrderRepository.setSnapshotUpdatedBy` | `/api/v1/orders/{orderId}/attribute` | `POST` | Body: `actorId`; in-place attribution only |
| `IOrderItemRepository.findActiveByOrderId` | `/api/v1/orders/{orderId}/items/active` | `GET` | Active items for snapshot |
| `IOrderItemRepository.findActiveByOrderIds` | `/api/v1/orders/items/active:batch` | `POST` | Body: `order_ids[]` |
| `IOrderItemRepository.findHistoryByOriginalId` | `/api/v1/order-items/by-original/{originalId}/history` | `GET` | Item version history |
| `IOrderItemRepository.create` | `/api/v1/orders/{orderId}/items` | `POST` | Create item snapshot |
| `IOrderItemRepository.update` | `/api/v1/order-items/{itemId}` | `PATCH` | Update item snapshot |
| `IOrderItemRepository.delete` | `/api/v1/order-items/{itemId}` | `DELETE` | Delete active item |
| `IOrderItemRepository.setSnapshotItemsUpdatedBy` | `/api/v1/orders/{orderId}/items/attribute` | `POST` | Body: `actorId` |

## Contract Mapping — Storage Preview

| Frontend source | Target endpoint | Method | Notes |
|---|---|---|---|
| `IStorageService.getFilePreviewSrc` | `/api/v1/storage/preview-url` | `POST` | Body: `path`, `bucket?`, `expiresInSeconds?`; returns signed URL |
| `IStorageService.getImagePreviewSrc` | `/api/v1/storage/preview-url` | `POST` | Same as file preview |

## Existing xScanner endpoints (keep compatible during migration)

- `/extract/upload`
- `/order/extract/upload`
- `/register`

These can stay as-is initially, then be versioned under `/api/v1` once frontend adapters are stable.

## First 3 Delivery Slices

## Slice 1 (recommended first): Orders read-only

Studio implementation note:

- A read-only order service adapter is available behind `VITE_USE_ORDERS_READ_API=true`.
- Current behavior for write operations still delegates to existing local service logic.

Slice 2 implementation note:

- Extraction read service adapter is available behind `VITE_USE_EXTRACTIONS_READ_API=true`.
- BIL read service adapter is available behind `VITE_USE_BIL_READ_API=true`.
- Mutation paths remain on existing local service paths until later slices.

Slice 3 implementation note:

- Extraction mutation adapter is available behind `VITE_USE_EXTRACTIONS_MUTATION_API=true`.
- It routes `validate`, `reject`, and `corrections` through server API while delegating read/extract methods to existing behavior.

Slice 4 implementation note:

- Auth API adapter is available behind `VITE_USE_AUTH_API=true`.
- It routes `sign-in`, `sign-up`, and `sign-out` through server API.
- Session bootstrap now routes through `authService.getSession()` and uses `/api/v1/auth/session` when auth API flag is enabled.

- Endpoints:
  - `GET /api/v1/orders`
  - `GET /api/v1/orders/status-counts`
  - `GET /api/v1/orders/by-original/{originalId}/active`
  - `GET /api/v1/orders/by-original/{originalId}/history`
- Frontend change: route read methods through `IOrderService` HTTP adapter.
- Tests:
  - server: contract tests for query filters + pagination + sort
  - frontend: integration tests for list/detail using mocked API responses

## Slice 2: Extractions read-only + BIL reads

- Endpoints:
  - `GET /api/v1/extractions`
  - `GET /api/v1/extractions/status-counts`
  - `GET /api/v1/extractions/by-original/{originalId}/active`
  - `GET /api/v1/extractions/by-original/{originalId}/history`
  - `GET /api/v1/bil/registrations`
  - `POST /api/v1/bil/registrations:batch`

## Slice 3: Extractions mutations

- Endpoints:
  - `POST /api/v1/extractions/{originalId}/validate`
  - `POST /api/v1/extractions/{originalId}/reject`
  - `POST /api/v1/extractions/{originalId}/corrections`

## Definition of Done per Slice

- Frontend has no direct persistence call for migrated paths.
- Server endpoint contract tests are green.
- Studio `check:fast` remains green.
- Integration tests added/updated for migrated user flows.
- Migration tracker updated with status and coverage impact.
