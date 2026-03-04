# xScanner Studio

Frontend repository for xScanner Studio (React + TypeScript + Vite) with local Supabase.

## Quick Start

```bash
npm install
make hooks-install
cp .env.example .env.local
make start-all
```

Studio runs on `http://localhost:8084`.

## Main Commands

```bash
make build
make lint
make hooks-install
make test-unit
make test-integration
make check-all
make supabase-start
make supabase-stop
```

Quality gate:
- Duplicate code is checked with `jscpd` (max `5%` in `src/**/*.{ts,tsx}`).
- If duplication is above 5%, `pre-commit` and `build` fail.
- CI also uploads a `duplicate-report` artifact (`reports/jscpd/`) for PR review.
- Direct Supabase runtime access in frontend UI layers is blocked by `npm run arch:check-no-direct-supabase` (included in `check:fast` and `check:all`).

Architecture direction:
- Studio is migrating to Variant B: frontend uses server APIs only, and persistence ownership moves fully to server side.
- See `docs/studio/ADR-0001-frontend-server-persistence-boundary.md` and `docs/studio/SERVICE_ARCHITECTURE.md`.

CI integration tests (optional):
- Trigger via PR label `ci:integration` or manual workflow dispatch (`run_integration=true`).
- Manual workflow dispatch runs integration tests only from `main`.
- Requires repository variable `XSCANNER_API_URL` pointing to a reachable xScanner API.

## Repository Scope

- This repository contains only the Studio frontend and Supabase resources.
- Python backend code lives in the original backend repository and is not part of this repo lifecycle.

## Documentation

- Architecture and design docs: `docs/studio/`
