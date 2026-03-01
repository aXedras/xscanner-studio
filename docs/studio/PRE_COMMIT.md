# Local Quality Checks — xScanner Studio

Use the repository root for all commands.

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
