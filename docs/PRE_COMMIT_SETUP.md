# Code Quality Automation

## 🔒 Automated Checks

**Pre-commit (every commit):**
- ✅ Code formatting (Ruff)
- ✅ Type checking (Mypy)
- ✅ DB types up-to-date (generated from migrations; see [PERSISTENCE.md](PERSISTENCE.md))
- ✅ Security checks (no private keys)
- ✅ Unit tests (fast, ~0.04s)
- ✅ Integration tests (mocked APIs, ~0.07s)

**Pre-push (before push):**
- ✅ E2E tests (real API calls, only if OPENAI_API_KEY is set)

## 📦 Installation (required for all developers)

```bash
# Install pre-commit
pip install pre-commit

# Activate hooks
pre-commit install
pre-commit install --hook-type pre-push

# Test
pre-commit run --all-files
```

## ✅ Verification

```bash
# Check if hook is installed
test -f .git/hooks/pre-commit && echo "✅ Installed" || echo "❌ Missing"

# Test with a commit
echo "test" > /tmp/test.txt
git add /tmp/test.txt
git commit -m "test: pre-commit hook"
# You should see hooks running!
```

## 🚫 Enforcement

**Local:**
- Hooks run automatically on `git commit` and `git push`
- Can be skipped with `--no-verify` (not recommended!)

**CI/CD:**
- GitHub Actions runs all checks on every PR
- Blocks PRs automatically if checks fail
- Cannot be bypassed

## 🔧 Workflow

**Commit:**
```bash
git commit -m "feat: new feature"
# → Runs: formatting, linting, type checking, unit tests, integration tests
```

**Push:**
```bash
git push
# → Runs: e2e tests (only if OPENAI_API_KEY is set, uses real API)
```

If auto-fixes are applied, re-stage and commit again.

## 🚨 Troubleshooting

**Hooks not running:**
```bash
pre-commit uninstall
pre-commit install
pre-commit install --hook-type pre-push
```

**Skip hooks (emergencies only):**
```bash
git commit --no-verify  # Skip pre-commit
git push --no-verify    # Skip pre-push
# ⚠️ CI will still check!
```

## 📊 Test Strategy

| Stage | Tests | Speed | API Keys Required |
|-------|-------|-------|-------------------|
| **Commit** | Unit + Integration | ~1.1s | ❌ No (mocked) |
| **Push** | E2E | ~5-15s | ✅ Yes (OPENAI_API_KEY) |
| **CI/CD** | All tests | ~1-2min | ✅ Yes (from secrets) |

**Test Types:**
- **Unit** (71 tests): Business logic, fast, no dependencies
- **Integration** (26 tests):
  - Strategy Integration (11): Service interfaces with mocked APIs
  - Server Integration (15): Real HTTP calls with FastAPI server
- **E2E** (3 tests): Real ChatGPT/Gemini API calls with ground truth validation

## ⚡ Quick Commands

```bash
# Run all hooks manually
pre-commit run --all-files

# Update hook versions
pre-commit autoupdate

# Run specific hook
pre-commit run ruff --all-files
```
