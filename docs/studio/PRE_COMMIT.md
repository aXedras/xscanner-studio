# Pre-Commit Setup — xScanner Studio

Code quality checks for the frontend application.

---

## Overview

**Studio uses the repository-wide pre-commit configuration** defined in `.pre-commit-config.yaml` at the repository root.

**Commit-stage hooks (run automatically on commit for Studio changes):**
- ✅ Formatting check (Prettier)
- ✅ Linting (ESLint)
- ✅ Type checking (TypeScript)
- ✅ Unit tests (Vitest)
- ✅ i18n validation
- ✅ DB types drift check (only when relevant files change)

**Pre-push hooks (run before push):**
- ✅ Server integration tests (pytest)
- ✅ Studio integration tests (Vitest; requires a running API)
- ✅ E2E tests (only if `OPENAI_API_KEY` is set)

Studio-specific hooks only run when `studio/` files are modified.

---

## Installation

```bash
# From repository root (recommended)
make dev
make studio-install

# Alternative (manual)
python -m pip install pre-commit
pre-commit install
pre-commit install --hook-type pre-push

# Studio deps
cd studio && npm install
```

That's it! Pre-commit hooks are now active for all commits.

---

## Package.json Scripts

Key scripts are already defined in `studio/package.json`.
Excerpt (for orientation):

```json
{
  "scripts": {
    "format": "prettier --write \"src/**/*.{ts,tsx,css,json}\"",
    "format:check": "prettier --check \"src/**/*.{ts,tsx,css,json}\"",
    "lint": "eslint .",
    "type-check": "tsc -b",
    "test:unit": "vitest run --dir tests/unit",
    "test:integration": "vitest run --dir tests/integration",
    "check:i18n:all": "node scripts/i18n/check-i18n.mjs && npm run check:i18n:missing && npm run check:i18n:unused",
    "db:check": "npm run db:types:check",
    "check:fast": "npm run lint && npm run type-check && npm run test:unit",
    "check:all": "npm run format:check && npm run lint && npm run type-check && npm run i18n:all && npm run db:check && npm run build && npm run test:unit"
  }
}
```

---

## Workflow

### Commit

```bash
git add .
git commit -m "feat: new feature"
```

**Runs automatically (only if `studio/` files changed):**
1. Prettier format check (`npm run format:check`)
2. ESLint linting (`npm run lint`)
3. TypeScript type check (`npm run type-check`)
4. Unit tests (`npm run test:unit`)
5. i18n validation (`npm run check:i18n:all`)
6. DB types drift check (only when relevant files changed)
7. JSON/YAML validation
8. Trailing whitespace removal

If any check fails → commit is blocked.

### Push

Before `git push`, pre-push hooks run integration tests. Studio integration tests require a running API and will fail fast if the API health check is not reachable.

### Skip Hooks (Emergency Only)

```bash
git commit --no-verify -m "fix: emergency hotfix"
```

**⚠️ Use sparingly!** Only for urgent fixes. Clean up immediately after.

---

## Configuration Files

### .prettierrc

```json
{
  "semi": false,
  "singleQuote": true,
  "tabWidth": 2,
  "trailingComma": "es5",
  "printWidth": 120,
  "arrowParens": "avoid"
}
```

### .prettierignore

```
node_modules/
dist/
build/
coverage/
*.min.js
*.min.css
```

### .eslintrc.cjs (already exists)

Already configured with:
- TypeScript support
- React rules
- Import rules

---

## Manual Commands

### Format code

```bash
npm run format
```

### Check formatting

```bash
npm run format:check
```

### Lint code

```bash
npm run lint
```

### Type check

```bash
npm run type-check
```

### Check i18n translations

```bash
npm run check:i18n:all
```

### Run tests

```bash
npm run test:all
```

### Run all checks

```bash
npm run check:all
```

---

## Skip Hooks (Emergency Only)

**Not recommended!** Bypasses quality checks.

```bash
git commit --no-verify
git push --no-verify
```

⚠️ **Use only in emergencies.** CI/CD will still run checks.

---

## CI/CD Integration

CI should run the same checks. See `.github/workflows/ci.yml` for the canonical pipeline.

---

## Troubleshooting

### Hooks not running

```bash
make hooks-install
```

### Run hooks manually

```bash
make hooks-run
```

### Format/Lint errors

```bash
# Auto-fix formatting
npm run format

# Auto-fix linting (where possible)
npm run lint -- --fix

# Check what's wrong
npm run format:check
npm run lint
```

### Type errors

Fix TypeScript errors manually. TypeScript cannot auto-fix type errors.

```bash
npm run type-check
```

---

## Best Practices

### DO ✅

1. **Run checks before committing**
   ```bash
   npm run format && npm run lint && npm test
   ```

2. **Fix issues immediately**
   - Don't commit broken code
   - Fix lint warnings
   - Add missing tests

3. **Keep commits small**
   - Easier to review
   - Easier to revert
   - Faster CI/CD

4. **Write meaningful commit messages**
   ```bash
   git commit -m "feat: add language switcher"
   git commit -m "fix: correct translation keys"
   ```

### DON'T ❌

1. **Don't skip hooks without reason**
   ```bash
   git commit --no-verify  # ❌ Avoid
   ```

2. **Don't commit console.log statements**
   ```typescript
   console.log('debug')  // ❌ Remove
   logger.debug('Component', 'debug info')  // ✅ Use logger
   ```

3. **Don't commit commented-out code**
   ```typescript
   // const oldFunction = () => {}  // ❌ Remove
   ```

4. **Don't commit large files**
   - Images → compress first
   - Dependencies → use package.json

---

## Quick Reference

| Command | Purpose |
|---------|---------|
| `npm run format` | Auto-format code |
| `npm run format:check` | Check formatting |
| `npm run lint` | Lint code |
| `npm run lint -- --fix` | Auto-fix linting |
| `npm run type-check` | TypeScript check |
| `npm run check:i18n` | Validate translations |
| `npm test` | Run tests (watch mode) |
| `npm test -- --run` | Run tests (once) |
| `npm run build` | Build for production |

---

## Related Documentation

- [TESTING.md](TESTING.md) — Testing strategy and patterns
- [LOGGING.md](LOGGING.md) — Logging best practices
- [I18N.md](I18N.md) — Internationalization guide
