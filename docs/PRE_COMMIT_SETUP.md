# Pre-commit Hooks Enforcement

## 🔒 Warum Pre-commit Hooks?

Pre-commit Hooks verhindern, dass Code mit Qualitätsproblemen committed wird:
- ✅ Automatisches Fixing von Import-Sortierung
- ✅ Code-Formatierung (Ruff)
- ✅ Type-Checking (Mypy)
- ✅ Security-Checks (keine Private Keys)

## 📦 Einmalige Installation (PFLICHT für alle Entwickler!)

```bash
# 1. Pre-commit installieren
pip install pre-commit

# 2. Hooks aktivieren (läuft automatisch bei jedem commit)
pre-commit install

# 3. Optional: Auch pre-push hook aktivieren
pre-commit install --hook-type pre-push

# 4. Testen
pre-commit run --all-files
```

## ✅ Verifikation

```bash
# Prüfen, ob Hook installiert ist
test -f .git/hooks/pre-commit && echo "✅ Installiert" || echo "❌ Fehlt"

# Test-Commit machen
echo "test" > /tmp/test.txt
git add /tmp/test.txt
git commit -m "test: pre-commit hook"
# Du solltest jetzt sehen, dass die Hooks laufen!
```

## 🚫 Hooks können NICHT umgangen werden (außer explizit)

**Lokale Enforcement:**
- Hooks laufen automatisch bei `git commit`
- Nur mit `--no-verify` übersprungbar (sollte NICHT gemacht werden!)

**Server-side Enforcement:**
1. **GitHub Actions CI** - separate Pre-commit Job (`.github/workflows/pre-commit.yml`)
   - Läuft IMMER, auch wenn lokale Hooks übersprungen wurden
   - Blockt PRs automatisch bei Failures

2. **Branch Protection Rules** (GitHub Settings):
   ```
   Settings → Branches → Branch protection rules
   ✅ Require status checks to pass before merging
   ✅ Require "Pre-commit Hooks" job to pass
   ```

## 🔧 Was passiert beim Commit?

```bash
git commit -m "feat: neue Funktion"

# Pre-commit läuft automatisch:
[INFO] Initializing environment...
[INFO] Running hook: trailing-whitespace...Passed
[INFO] Running hook: end-of-file-fixer...Passed
[INFO] Running hook: check-yaml...Passed
[INFO] Running hook: ruff...Passed (with fixes)
[INFO] Running hook: ruff-format...Passed
[INFO] Running hook: mypy...Passed

# Falls Änderungen gemacht wurden (z.B. Import-Sortierung):
[WARNING] Ruff fixed files, please review changes and commit again

# Du musst dann nochmal committen:
git add -u
git commit -m "feat: neue Funktion"
```

## 🚨 Troubleshooting

### Hook läuft nicht?

```bash
# Neu installieren
pre-commit uninstall
pre-commit install

# Cache löschen
pre-commit clean
pre-commit run --all-files
```

### Hooks überspringen (NUR in Notfällen!)

```bash
git commit --no-verify -m "emergency fix"
# ⚠️ Aber: CI wird trotzdem prüfen und ggf. blockieren!
```

### Hooks sind zu langsam?

```bash
# Nur auf geänderte Dateien laufen lassen
git commit  # Standard Verhalten

# Alle Dateien (z.B. nach Config-Änderung)
pre-commit run --all-files
```

## 📊 Status

| Enforcement Layer | Status | Bypass möglich? |
|-------------------|--------|-----------------|
| Lokale Pre-commit Hooks | ✅ Aktiv | ⚠️ Ja mit `--no-verify` |
| GitHub Actions Pre-commit Job | ✅ Aktiv | ❌ Nein |
| GitHub Branch Protection | ⏳ TODO | ❌ Nein (wenn aktiviert) |

## 🎯 Nächste Schritte

1. **Alle Entwickler:** Pre-commit installieren (siehe oben)
2. **Repository Admin:** Branch Protection aktivieren in GitHub Settings
3. **Team:** Bei jedem PR sicherstellen, dass Pre-commit Job ✅ ist

## ⚡ Pro-Tipps

```bash
# Nur bestimmte Hooks laufen lassen
pre-commit run ruff --all-files

# Hook-Updates holen
pre-commit autoupdate

# Pre-commit in CI simulieren
pre-commit run --all-files --show-diff-on-failure
```

---

**Frage?** Siehe [Contributing Guidelines](CONTRIBUTING.md) oder frag im Team-Chat.
