# Studio Docs Conventions

This guide keeps documentation in `docs/studio` lean, navigable, and maintainable.

## 1) Document Types

### Active Docs

Use for day-to-day engineering work and current system behavior.

Examples:

- `UI_ARCHITECTURE.md`
- `SERVICE_ARCHITECTURE.md`
- `TESTING.md`
- `LOGGING.md`

### Historical Docs

Use for migration rationale, handoff context, and implementation history.

Examples:

- `*_VARIANT_B.md`
- `SLICE*_ONE_GO.md`

Historical docs must never be the only source of truth for current runtime behavior.

## 2) Required Metadata Header

Every document should include this section near the top:

```md
## Document Metadata

- Status: Active | Historical
- Audience: <who should read this>
- Use this when: <primary usage>
- Source of truth for current behavior: <active doc(s)>
- Last reviewed: YYYY-MM-DD
```

## 3) Minimal Writing Template

Use this structure for new docs:

```md
# <Title>

## Document Metadata
- ...

## Purpose

## Scope

## Details

## Verification / Checks

## Related Docs
```

## 4) Keep Docs Small and Composable

- Prefer short focused docs over monolithic specs.
- Move duplicated sections into a single canonical document.
- Link instead of copying large blocks.

## 5) Update Rules

When changing behavior in code:

1. Update the relevant active doc(s).
2. If historical docs become misleading, add a short note pointing to current source of truth.
3. Refresh `Last reviewed` date in touched docs.

## 6) Index Hygiene

`docs/studio/README.md` is the entrypoint.

- Keep "Start Here" focused on active docs.
- Keep migration docs grouped under "Historical / Migration Docs".
- Avoid adding deep implementation details directly to the index.
