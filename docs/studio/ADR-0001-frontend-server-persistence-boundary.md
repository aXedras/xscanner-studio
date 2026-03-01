# ADR-0001 — Frontend/Server Persistence Boundary

## Status

Accepted (2026-03-01)

## Context

xScanner Studio currently performs persistence through Supabase access in the frontend codebase.

This creates split ownership concerns with the Python server codebase, where persistence logic is also required. If both systems can independently evolve persistence behavior, drift and operational ambiguity are likely.

## Decision

Adopt **Variant B** as the target architecture:

- Frontend accesses data **only through server APIs**.
- Frontend performs **no direct persistence access** (database/storage/auth persistence APIs).
- Server becomes the single owner of persistence orchestration and data integrity.

## Consequences

### Positive

- Single write authority and consistent persistence rules.
- Clear separation of concerns (UI vs business/persistence orchestration).
- Better long-term maintainability and auditability.

### Trade-offs

- Requires API surface expansion on the server.
- Requires iterative migration of frontend services/repositories.
- Temporary transitional exceptions may exist and must be tracked explicitly.

## Architecture Rule (Guardrail)

- New direct Supabase runtime usage in UI layers is forbidden.
- Guard check: `npm run arch:check-no-direct-supabase`.
- This guard is included in `check:fast` and `check:all`.

Temporary exceptions are explicitly listed in `scripts/check-no-direct-supabase.mjs` and must be reduced over time.

## Design Principles

- SOLID boundaries:
  - UI: presentation + interaction state only.
  - Service layer: use-case orchestration through interfaces.
  - Infrastructure: API clients only (no local DB access in UI codebase).
- Clean Code:
  - Explicit contracts and error semantics.
  - No hidden fallbacks that bypass architectural boundaries.
- GOF usage where useful:
  - Adapter (migrate old clients to new API contracts)
  - Facade (per-domain API access point)
  - Strategy (retry/backoff/polling behavior)

## Verification Criteria

- Build, lint, and tests remain green after each migration slice.
- Test coverage is expanded incrementally per migrated slice (contract + integration + unit where appropriate).
- Direct Supabase usage in frontend UI layers trends toward zero.
