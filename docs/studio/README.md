# Studio Documentation

This folder contains technical documentation for **xScanner Studio** (frontend).

## Start Here (Active Docs)

### Architecture & Design

- [UI_ARCHITECTURE.md](UI_ARCHITECTURE.md) – UI structure, routing, page composition
- [SERVICE_ARCHITECTURE.md](SERVICE_ARCHITECTURE.md) – service layer, adapters, runtime wiring
- [DESIGN_SYSTEM.md](DESIGN_SYSTEM.md) – design tokens, component styling conventions
- [ADR-0001-frontend-server-persistence-boundary.md](ADR-0001-frontend-server-persistence-boundary.md) – architectural decision record

### Engineering Practices

- [TESTING.md](TESTING.md) – testing strategy and commands
- [LOGGING.md](LOGGING.md) – logging standards and usage
- [I18N.md](I18N.md) – translation structure and i18n workflow
- [PRE_COMMIT.md](PRE_COMMIT.md) – local quality gates and hooks
- [DOCS_CONVENTIONS.md](DOCS_CONVENTIONS.md) – lightweight writing template and document lifecycle rules

### API Contracts

- [openapi/auth-v1.yaml](openapi/auth-v1.yaml) – auth/session API contract used by Studio

## History

- Historical Variant-B migration docs were removed on 2026-03-04.
- Reason: reduce documentation noise and stale handoff artifacts.
- If needed, use git history for legacy rollout context.
- Current source of truth: active docs in this folder + `openapi/auth-v1.yaml`.

## Practical Rule of Thumb

- Building or changing frontend behavior: start with `UI_ARCHITECTURE.md` + `SERVICE_ARCHITECTURE.md`
- Changing quality/dev workflow: use `TESTING.md`, `LOGGING.md`, `PRE_COMMIT.md`
- Checking auth API behavior: use `openapi/auth-v1.yaml`
- Investigating old rationale: inspect git history
