# Pre-Commit Setup — xScanner Studio

Code quality checks for the frontend application.

---

## Overview

**Studio uses the repository-wide pre-commit configuration** defined in `.pre-commit-config.yaml` at the repository root.

**Pre-commit hooks (run automatically on commit):**
- ✅ Code formatting (Prettier)
- ✅ Linting (ESLint)
- ✅ Type checking (TypeScript)
- ✅ i18n validation
- ✅ JSON/YAML validation
- ✅ Trailing whitespace removal

**All hooks only run when studio/ files are modified.**

---

## Installation

```bash
# From repository root
pip install pre-commit
pre-commit install

# Install Studio dependencies
cd studio/
npm install
```

That's it! Pre-commit hooks are now active for all commits.

---

## Package.json Scripts

Add these scripts to `package.json`:

```json
{
  "scripts": {
    "format": "prettier --write \"src/**/*.{ts,tsx,css,json}\"",
    "format:check": "prettier --check \"src/**/*.{ts,tsx,css,json}\"",
    "lint": "eslint src --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
    "type-check": "tsc --noEmit",
    "check:i18n": "node scripts/check-i18n.mjs",
    "test": "vitest",
    "test:run": "vitest run",
    "test:unit": "vitest run --dir tests/unit",
    "test:integration": "vitest run --dir tests/integration",
    "test:ci": "npm run test:unit && npm run test:integration",
    "test:coverage": "vitest --coverage",
    "build": "tsc && vite build",
    "prepare": "husky install"
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

**Runs automatically (only if studio/ files changed):**
1. Prettier format check (`npm run format:check`)
2. ESLint linting (`npm run lint`)
3. TypeScript type check (`npm run type-check`)
4. Unit tests (`npm run test:unit`)
5. Integration tests (`npm run test:integration`)
6. i18n validation (`npm run check:i18n:all`)
7. JSON/YAML validation
8. Trailing whitespace removal

If any check fails → commit is blocked.

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
npm run check:i18n
```

### Run tests

```bash
npm run test:ci
```

### Run all checks

```bash
npm run format:check && npm run lint && npm run type-check && npm test -- --run
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

GitHub Actions should run the same checks:

```yaml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 18
          cache: 'npm'
          cache-dependency-path: studio/package-lock.json

      - name: Install dependencies
        working-directory: studio
        run: npm ci

      - name: Check formatting
        working-directory: studio
        run: npm run format:check

      - name: Lint
        working-directory: studio
        run: npm run lint

      - name: Type check
        working-directory: studio
        run: npm run type-check

      - name: Run tests
        working-directory: studio
        run: npm test -- --run

      - name: Build
        working-directory: studio
        run: npm run build
```

---

## Troubleshooting

### Hooks not running

```bash
# Reinstall Husky
rm -rf .husky
npx husky init
# Re-create hooks (see Installation section)
```

### "command not found: husky"

```bash
npm install -D husky
npx husky init
```

### "Permission denied"

```bash
chmod +x .husky/pre-commit
chmod +x .husky/pre-push
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
