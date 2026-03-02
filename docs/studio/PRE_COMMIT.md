# Local Quality Checks — xScanner Studio

Use the repository root for all commands.

## Git Hooks (recommended)

Activate managed hooks from this repository:

```bash
make hooks-install
```

This configures `core.hooksPath=.githooks` and enables the tracked `pre-commit` hook.
The hook runs:

```bash
npm run check:pre-commit
```

`check:pre-commit` enforces:

- `prettier --check` formatting gate
- duplicate detection via `jscpd`
- architecture guard: no direct UI Supabase runtime access
- architecture guard: Supabase DB calls (`supabase.from(...)` / `supabase.rpc(...)`) only in repository/persistence layers
- i18n key consistency checks across language files
- ESLint + TypeScript + unit tests

Policy: maximum `5%` duplication in `src/**/*.{ts,tsx}`.
If duplication is above 5%, pre-commit fails.

Disable again (if needed):

```bash
make hooks-uninstall
```

## Install

```bash
npm install
```

## Fast Check

```bash
npm run check:fast
```

Runs:
- ESLint
- TypeScript type-check
- Unit tests

## Full Check (CI-equivalent)

```bash
npm run check:all
```

Runs:
- Prettier format check
- ESLint
- TypeScript type-check
- i18n checks
- Supabase DB types drift check
- Build
- Unit tests

## Integration Tests

```bash
npm run test:integration
```

Requires:
- Running xScanner API (external backend repository)
- Running local Supabase (`supabase start`)
- Optional `.env.local` with `VITE_API_URL`
