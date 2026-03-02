# Migration Plan — Variant B (Server Owns Persistence)

This document defines the step-by-step migration from frontend-managed persistence to server-owned persistence.

Related execution docs:

- `API_CONTRACT_BACKLOG_VARIANT_B.md`
- `SERVER_REPO_PLAYBOOK_VARIANT_B.md`

## Target State

- Studio frontend talks only to server APIs.
- Persistence logic lives on server side.
- Frontend no longer depends on runtime Supabase clients for domain persistence.

## Non-Functional Constraints

- No big-bang migration.
- Keep `build`, `lint`, and tests green after each slice.
- Expand test coverage systematically while migrating.

## Current Inventory (Frontend)

### Direct runtime Supabase usage (transitional)

- None in UI layer.

### Supabase-backed domain repositories/services in frontend

- `src/services/core/auth/repository/SupabaseAuthRepository.ts`
- `src/services/core/extraction/repository/SupabaseExtractionRepository.ts`
- `src/services/core/extraction/repository/SupabaseBilRegistrationRepository.ts`
- `src/services/core/order/repository/SupabaseOrderRepository.ts`
- `src/services/core/order/repository/SupabaseOrderItemRepository.ts`
- `src/services/core/storage/impl/StorageService.ts`
- `src/services/infrastructure/persistence/SupabaseCrudRepository.ts`
- `src/services/index.ts` (wiring with Supabase client)

### Frontend Supabase library files

- `src/lib/supabase/client.ts`
- `src/lib/supabase/index.ts`
- `src/lib/supabase/database.types.ts`

## Migration Phases

## Phase 0 — Guardrails and Decision Baseline (DONE)

- ADR accepted: `ADR-0001-frontend-server-persistence-boundary.md`
- Guardrail active: `npm run arch:check-no-direct-supabase`

## Phase 1 — Contract-First API Design

For each domain, define API contracts before implementation:

- Auth/session
- Orders (list/detail/mutations)
- Extractions (list/detail/mutations)
- BIL registrations
- Storage operations currently initiated from frontend

Deliverables:

- Endpoint list + DTOs + error semantics.
- Migration mapping table: frontend method → server endpoint.

## Phase 2 — Server Endpoints + Contract Tests

Implement endpoints server-side first.

Deliverables:

- Server repository/use-case wiring.
- Contract tests for all new endpoints.

## Phase 3 — Frontend Adapters (Strangler)

Replace frontend Supabase repositories with API adapters, domain by domain.

Suggested order:

1. Read paths (lists/details)
2. Write paths (mutations)
3. Auth/session
4. Storage

Deliverables:

- Per-domain adapter classes using server API clients.
- Feature-level migration switches removed once stable.

## Phase 4 — Remove Frontend Supabase Runtime Usage

After all domain paths are migrated:

- Remove runtime Supabase client usage from `App.tsx` and `Layout.tsx`.
- Remove obsolete Supabase repositories and persistence infrastructure.

Deliverables:

- No runtime Supabase access outside explicitly accepted temporary exceptions.
- Exceptions list reaches zero.

## Phase 5 — Cleanup and Dependency Reduction

- Remove unused frontend Supabase dependencies if no longer needed.
- Simplify service wiring and update architecture docs.

## Test & Quality Expansion Plan

For each migrated slice:

1. Add/update API contract tests.
2. Add frontend integration tests against the API contract.
3. Keep or add targeted unit tests for local mapping/error handling.

Minimum acceptance per slice:

- `npm run check:fast` passes.
- Relevant integration tests pass.
- Coverage for touched modules does not regress.

## Current Implementation Status (2026-03-01)

Completed in Studio:

- Service-layer HTTP adapters are in place for:
	- Orders read (`HttpOrderReadService`)
	- Extractions read (`HttpExtractionReadService`)
	- BIL read (`HttpBilReadService`)
	- Extractions mutation (`HttpExtractionMutationService`)
	- Auth (`HttpAuthRepository` via `AuthService`)
- `ServiceFactory` wiring now applies HTTP adapters at service boundaries only.
- Repository-level HTTP adapters were removed to keep repositories local/internal.
- App session bootstrap now uses `authService.getSession()` with auth-session refresh events.

Feature flags currently used:

- `VITE_USE_ORDERS_READ_API`
- `VITE_USE_EXTRACTIONS_READ_API`
- `VITE_USE_BIL_READ_API`
- `VITE_USE_EXTRACTIONS_MUTATION_API`
- `VITE_USE_AUTH_API`

Latest validation snapshot:

- `npm run test:unit`: 25/25 tests passing.
- `npm run check:fast`: passing.

## Next Slice (Short List)

1. Add Studio integration tests for Orders/Extractions read flows with API-mocked responses while the read flags are enabled.
2. Implement server contract tests for the already mapped read endpoints (`/api/v1/orders*`, `/api/v1/extractions*`, `/api/v1/bil/registrations*`) to lock query/filter semantics.
3. Start auth/session migration by introducing frontend service-level API adapters for sign-in/sign-out/session and removing direct runtime Supabase reads from app/session bootstrap paths.

## Tracking

Track migration per method in a checklist table (to be updated during implementation):

- Method name
- Current implementation owner (frontend/server)
- Target endpoint
- Test coverage status
- Migration status
