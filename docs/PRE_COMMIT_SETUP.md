# Code Quality Automation

## 🔒 Automated Checks

**Pre-commit (every commit):**
- ✅ Code formatting (Ruff)
- ✅ Type checking (Mypy)
- ✅ Security checks (no private keys)
- ✅ Unit tests (fast, ~0.04s)

**Pre-push (before push):**
- ✅ Integration tests (requires API keys)

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
# → Runs: formatting, linting, type checking, unit tests
```

**Push:**
```bash
git push
# → Runs: integration tests (needs API keys)
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

| Stage | Tests | Speed | Required |
|-------|-------|-------|----------|
| **Commit** | Unit tests | ~0.04s | ✅ Always |
| **Push** | Integration tests | ~2-5s | ✅ With API keys |

**Why two stages?**
- Fast feedback on every commit
- Comprehensive validation before sharing code

## ⚡ Quick Commands

```bash
# Run all hooks manually
pre-commit run --all-files

# Update hook versions
pre-commit autoupdate

# Run specific hook
pre-commit run ruff --all-files
```
