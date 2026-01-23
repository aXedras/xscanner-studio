.PHONY: help install dev venv hooks hooks-install hooks-update hooks-run format lint check check-help check-fast check-all studio studio-install studio-format-check studio-lint studio-type-check studio-i18n-check studio-db-types-check studio-build studio-test-unit studio-test-integration studio-check-fast studio-check-all test test-help test-all test-unit test-integration test-e2e test-coverage test-quick pre-commit-all db-types db-types-generate db-types-check database database-start database-stop start start-server start-studio start-supabase start-all preprod preprod-check preprod-update-main preprod-up preprod-down preprod-health preprod-status preprod-logs preprod-deploy release release-help release-create release-status release-list version ci-main-status docker-build docker-run clean cli cli-help cli cli-interactive cli-test cli-list-images cli-list-strategies cli-benchmark cli-benchmark-quick cli-report cli-report-history

# Load environment variables from .env.local
-include .env.local
export

# Virtualenv (cross-platform)
VENV_DIR := venv
ifeq ($(OS),Windows_NT)
VENV_PYTHON := $(VENV_DIR)/Scripts/python.exe
else
VENV_PYTHON := $(VENV_DIR)/bin/python
endif

# Extract Studio port from vite.config.ts (best-effort)
ifeq ($(OS),Windows_NT)
STUDIO_PORT := 8084
else
STUDIO_PORT := $(shell grep -oP 'port:\s*\K\d+' studio/vite.config.ts 2>/dev/null || echo 8084)
endif

# Install production dependencies
venv:

ifeq ($(OS),Windows_NT)
	@if not exist "$(VENV_PYTHON)" (python -m venv $(VENV_DIR))
else
	@if [ ! -x "$(VENV_PYTHON)" ]; then python3 -m venv $(VENV_DIR); fi
endif
	@$(VENV_PYTHON) -m pip install -U pip

install: venv
	@$(VENV_PYTHON) -m pip install -e .

# Show an overview of the most important commands
help:
	@echo "xScanner Make Targets"
	@echo "  make start     # dev services help"
	@echo "  make database  # Supabase start/stop help"
	@echo "  make preprod   # pre-prod deploy help"
	@echo "  make release   # release help"
	@echo "  make version   # show local version + latest GitHub release"
	@echo "  make studio    # studio targets help"
	@echo "  make check     # check targets help"
	@echo "  make check-fast # fast local checks (lint + unit tests)"
	@echo "  make check-all  # full local CI script (mirrors GitHub Actions)"
	@echo "  make test      # test targets help"
	@echo "  make cli       # CLI help"
	@echo "  make db-types  # DB types help"
	@echo "  make hooks     # pre-commit hooks help"

# Install with server dependencies
install-server: venv
	@$(VENV_PYTHON) -m pip install -e ".[server]"

# Install development dependencies
dev: venv
	@$(VENV_PYTHON) -m pip install -e ".[dev]"
	@make hooks-install

hooks:
	@echo "🪝 Git Hooks (pre-commit)"
	@echo ""
	@echo "  make hooks-install   Install pre-commit + git hooks (pre-commit + pre-push)"
	@echo "  make hooks-run       Run commit-stage hooks on all files"
	@echo "  make hooks-update    Update hook versions in .pre-commit-config.yaml"
	@echo ""
	@echo "Notes:"
	@echo "  - Hooks run automatically on commit/push after install."
	@echo "  - We install pre-commit into the repo venv (venv/)."

hooks-install: venv
	@$(VENV_PYTHON) -m pip install -U pre-commit
	@$(VENV_PYTHON) -m pre_commit install
	@$(VENV_PYTHON) -m pre_commit install --hook-type pre-push

hooks-update: venv
	@$(VENV_PYTHON) -m pre_commit autoupdate

hooks-run: venv
	@$(VENV_PYTHON) -m pre_commit run --all-files

# Format code
format:
	@$(VENV_PYTHON) -m ruff format .
	@$(VENV_PYTHON) -m ruff check --fix .

# Lint code (no fixes)
lint: db-types-check
	@$(VENV_PYTHON) -m ruff check .
	@$(VENV_PYTHON) -m ruff format --check .
	@$(VENV_PYTHON) -m mypy src/xscanner/ --ignore-missing-imports

# DB types (server)
db-types:
	@echo "🧬 Server DB Types"
	@echo ""
	@echo "  make db-types-generate   Generate src/xscanner/server/db_types.py"
	@echo "  make db-types-check      Verify DB types match supabase/migrations"

db-types-generate:
	@$(VENV_PYTHON) -m scripts.db.gen_db_types

db-types-check:
	@$(VENV_PYTHON) -m scripts.db.check_db_types

# Checks (help)
check: check-help

check-help:
	@echo "✅ Check Targets"
	@echo ""
	@echo "  make check-fast        Fast local checks (Server + Studio, no Supabase)"
	@echo "  make check-all         Full local CI script (mirrors GitHub Actions)"
	@echo "  make studio-check-fast Studio fast checks (lint/type/unit)"
	@echo "  make studio-check-all  Studio full checks (format/i18n/dbtypes/build/unit)"
	@echo ""
	@echo "Individual checks:"
	@echo "  make lint         Ruff + mypy + DB types check"
	@echo "  make db-types-check"
	@echo "  make test-quick    Unit tests (quick)"
	@echo "  make test-unit     Unit tests (verbose)"
	@echo "  make test-integration"
	@echo "  make test-e2e"
	@echo ""
	@echo "Notes:"
	@echo "  - check-all runs scripts/ci-check-local.sh and may require Node, Supabase, and API keys."

# Fast local checks (suitable for day-to-day development)
check-fast: lint test-quick studio-check-fast
	@echo "✅ Fast checks passed locally!"

# Full CI run (mirrors GitHub Actions; may require Node, Supabase, and API keys for some checks)
check-all:

ifeq ($(OS),Windows_NT)
	@where bash >NUL 2>&1 || (echo bash not found. Install Git Bash or use WSL to run check-all. & exit /b 1)
	@bash scripts/ci-check-local.sh
else
	@bash scripts/ci-check-local.sh
endif

studio:
	@echo "🎛️  xScanner Studio"
	@echo ""
	@echo "Prefer npm-first when working on Studio:"
	@echo "  cd studio && npm run help"
	@echo "  cd studio && npm run check"
	@echo "  cd studio && npm run check:fast"
	@echo ""
	@echo "Setup:"
	@echo "  make studio-install          Install dependencies (local dev)"
	@echo ""
	@echo "Fast checks:"
	@echo "  make studio-check-fast       Lint + type-check + unit tests"
	@echo "  make studio-check-all        Full checks (format/i18n/dbtypes/build/unit)"
	@echo ""
	@echo "Individual commands:"
	@echo "  make studio-format-check     Prettier check"
	@echo "  make studio-lint             ESLint"
	@echo "  make studio-type-check       TypeScript type-check"
	@echo "  make studio-i18n-check       i18n checks"
	@echo "  make studio-db-types-check   Supabase DB types drift check"
	@echo "  make studio-build            Build"
	@echo "  make studio-test-unit        Unit tests"
	@echo "  make studio-test-integration Integration tests (requires running server + Supabase env)"

studio-install:
ifeq ($(OS),Windows_NT)
	@if not exist studio (echo Studio folder not found.& exit /b 1)
	@where npm >NUL 2>&1 || (echo npm not found (required for Studio) & exit /b 1)
	@cd studio && npm install
else
	@if [ ! -d "studio" ]; then echo "Studio folder not found."; exit 1; fi
	@if ! command -v npm >/dev/null 2>&1; then echo "npm not found (required for Studio)" >&2; exit 1; fi
	@cd studio && npm install
endif

studio-format-check:
	@cd studio && npm run format:check

studio-lint:
	@cd studio && npm run lint

studio-type-check:
	@cd studio && npm run type-check

studio-i18n-check:
	@cd studio && npm run check:i18n:all

studio-db-types-check:
	@cd studio && npm run db:check

studio-build:
	@cd studio && npm run build

studio-test-unit:
	@cd studio && npm run test:unit

studio-test-integration:
	@cd studio && npm run test:integration

studio-check-fast:
ifeq ($(OS),Windows_NT)
	@if exist studio (cd studio && npm run check:fast) else (echo Studio folder not found, skipping.)
else
	@if [ ! -d "studio" ]; then echo "Studio folder not found, skipping."; exit 0; fi
	@if ! command -v npm >/dev/null 2>&1; then echo "npm not found (required for Studio checks)" >&2; exit 1; fi
	@cd studio && npm run check:fast
endif

studio-check-all:
ifeq ($(OS),Windows_NT)
	@if exist studio (cd studio && npm run check:all) else (echo Studio folder not found, skipping.)
else
	@if [ ! -d "studio" ]; then echo "Studio folder not found, skipping."; exit 0; fi
	@if ! command -v npm >/dev/null 2>&1; then echo "npm not found (required for Studio checks)" >&2; exit 1; fi
	@cd studio && npm run check:all
endif

# Run pre-commit on all files (what pre-commit hook does)
pre-commit-all:
	@$(VENV_PYTHON) -m pre_commit run --all-files

# Run tests (help)
test: test-help

test-help:
	@echo "🧪 Available test targets:"
	@echo ""
	@echo "  make test-all          Run ALL tests (unit + integration + e2e)"
	@echo "  make test-unit         Run only unit tests (fast)"
	@echo "  make test-integration  Run only integration tests"
	@echo "  make test-e2e          Run only e2e tests"
	@echo "  make test-coverage     Run tests with coverage report"
	@echo "  make test-quick        Run quick tests (unit only)"
	@echo ""
	@echo "Examples:"
	@echo "  make test-unit         # Fast feedback during development"
	@echo "  make test-e2e          # Test with real API calls"
	@echo "  make cli-interactive   # Quality check via interactive CLI"

# Run ALL tests
test-all:
	@echo "🧪 Running all tests (unit + integration + e2e)..."
	@$(VENV_PYTHON) -m pytest tests/ -v

# Run only fast unit tests
test-unit:
	@echo "⚡ Running unit tests only..."
	@$(VENV_PYTHON) -m pytest tests/unit/ -v

# Run only integration tests
test-integration:
	@echo "🔌 Running integration tests (mocked APIs, no API keys needed)..."
	@$(VENV_PYTHON) -m pytest tests/integration/ -v -m integration

# Run only e2e tests
test-e2e:
	@echo "🚀 Running e2e tests (requires API keys & services)..."
	@$(VENV_PYTHON) -m pytest tests/e2e/ -v -m e2e

# Run tests with coverage report
test-coverage:
	@echo "📊 Running tests with coverage..."
	@$(VENV_PYTHON) -m pytest tests/ --cov=src/xscanner --cov-report=html --cov-report=term
	@echo ""
	@echo "✅ Coverage report generated: htmlcov/index.html"

# Run quick tests (unit only, for pre-commit)
test-quick:
	@echo "⚡ Running quick tests..."
	@$(VENV_PYTHON) -m pytest tests/unit/ -q

# Start services (show help)
start:
	@echo "🚀 xScanner Services"
	@echo ""
	@echo "Available start commands:"
	@echo ""
	@echo "  make start-supabase  Start/check Supabase"
	@echo "  make start-server    Start FastAPI backend"
	@echo "  make start-studio    Start Vite UI"
	@echo "  make start-all       Start all services (Supabase + Server + Studio)"
	@echo ""
	@echo "Prerequisites:"
	@echo "  • Python:    source venv/bin/activate"
	@echo "  • Node:      cd studio && npm install"
	@echo ""
ifeq ($(OS),Windows_NT)
	@echo "Windows notes:"
	@echo "  • Python:    venv\\Scripts\\activate"
	@echo "  • Some targets require Git Bash (bash) or WSL"
endif

# Start FastAPI backend
start-server:

ifeq ($(OS),Windows_NT)
	@scripts\\windows\\development\\start-server.bat
else
	@bash scripts/development/start-server.sh
endif

# Start Vite studio UI
start-studio:
	@cd studio && npm run dev

# Start or check Supabase
start-supabase:
	@$(MAKE) database-start

# Database (Supabase) commands
database:
	@echo "🗄️  Database (Supabase)"
	@echo ""
	@echo "Available database commands:"
	@echo ""
	@echo "  make database-start   Start/check Supabase"
	@echo "  make database-stop    Stop Supabase"
	@echo ""
	@echo "Notes:"
	@echo "  - preprod-down intentionally keeps Supabase running"

database-start:
ifeq ($(OS),Windows_NT)
	@scripts\\windows\\preprod\\database-start.bat
else
	@bash scripts/preprod/database-start.sh
endif

database-stop:
ifeq ($(OS),Windows_NT)
	@scripts\\windows\\preprod\\database-stop.bat
else
	@bash scripts/preprod/database-stop.sh
endif

preprod:
	@echo "🚀 xScanner Pre-prod"
	@echo ""
	@echo "Available pre-prod commands:"
	@echo ""
	@echo "  make preprod-check         Validate prerequisites (.env.preprod, docker, supabase)"
	@echo "  make preprod-update-main   Fetch + checkout main + pull --ff-only"
	@echo "  make preprod-up            Start/upgrade API+Studio via docker-compose.preprod.yml"
	@echo "  make preprod-down          Stop API+Studio (keeps Supabase running)"
	@echo "  make preprod-health        Run /health check against pre-prod API"
	@echo "  make preprod-status        Show supabase status + docker compose ps"
	@echo "  make preprod-logs          Tail docker compose logs"
	@echo "  make preprod-deploy        Deploy (default: latest GitHub release)"
	@echo ""
	@echo "Deploy options:"
	@echo "  - ORIGIN=main|latest|release-x.y.z (default: latest)"
	@echo "  - MODE=cloud|full (default: full for releases, cloud for main)"
	@echo ""
	@echo "Examples:"
	@echo "  make preprod-deploy                         # ORIGIN=latest, MODE=full"
	@echo "  make preprod-deploy MODE=cloud              # latest release, cloud image"
	@echo "  make preprod-deploy ORIGIN=release-0.1.0    # pin release tag v0.1.0 (full)"
	@echo "  make preprod-deploy ORIGIN=release-0.1.0 MODE=cloud"
	@echo "  make preprod-deploy ORIGIN=main MODE=cloud  # main HEAD, local build (cloud)"
	@echo "  make preprod-deploy ORIGIN=main MODE=full   # main HEAD, local build (full)"
	@echo ""
	@echo "Env files:"
	@echo "  .env.preprod.example -> .env.preprod (do not commit secrets)"

preprod-check:

ifeq ($(OS),Windows_NT)
	@where bash >NUL 2>&1 || (echo bash not found. Use WSL/Git Bash for preprod targets (except database-start/stop/deploy). & exit /b 1)
	@bash scripts/preprod/check.sh
else
	@bash scripts/preprod/check.sh
endif

preprod-update-main:

ifeq ($(OS),Windows_NT)
	@where bash >NUL 2>&1 || (echo bash not found. Use WSL/Git Bash for preprod targets (except database-start/stop/deploy). & exit /b 1)
	@bash scripts/preprod/update-main.sh
else
	@bash scripts/preprod/update-main.sh
endif

preprod-up:

ifeq ($(OS),Windows_NT)
	@scripts\\windows\\preprod\\database-start.bat
	@scripts\\windows\\preprod\\up.bat
else
	@bash scripts/preprod/database-start.sh
	@bash scripts/preprod/up.sh
endif

preprod-down:

ifeq ($(OS),Windows_NT)
	@scripts\\windows\\preprod\\down.bat
else
	@bash scripts/preprod/down.sh
endif

preprod-health:

ifeq ($(OS),Windows_NT)
	@scripts\\windows\\preprod\\health.bat
else
	@bash scripts/preprod/health.sh
endif

preprod-status:

ifeq ($(OS),Windows_NT)
	@scripts\\windows\\preprod\\status.bat
else
	@bash scripts/preprod/status.sh
endif

preprod-logs:

ifeq ($(OS),Windows_NT)
	@scripts\\windows\\preprod\\logs.bat
else
	@bash scripts/preprod/logs.sh
endif

preprod-deploy:

ifeq ($(OS),Windows_NT)
	@scripts\\windows\\preprod\\deploy.bat
else
	@bash scripts/preprod/deploy.sh
endif

# Releases
release:
	@echo "🏷️  xScanner Release"
	@echo ""
	@echo "Commands:"
	@echo "  make release-create        Create GitHub release (tag + release)"
	@echo "  make release-status        Show latest GitHub release + list releases"
	@echo ""
	@echo "Usage:"
	@echo "  make release-create VERSION=X.Y.Z"
	@echo "  make release-status [LIMIT=20]"
	@echo ""
	@echo "Notes:"
	@echo "  - Runs scripts/release/create-release.sh"
	@echo "  - Requires clean working tree on main + gh auth"
	@echo "  - Enforces docs/CHANGELOG.md + version alignment"

release-help: release

release-create:
	$(if $(strip $(VERSION)),,$(error VERSION is required. Usage: make release-create VERSION=X.Y.Z))

ifeq ($(OS),Windows_NT)
	@where bash >NUL 2>&1 || (echo bash not found. Use WSL/Git Bash to run release-create. & exit /b 1)
	@VERSION="$(VERSION)" bash scripts/release/create-release.sh
else
	@VERSION="$(VERSION)" bash scripts/release/create-release.sh
endif

release-list:
ifeq ($(OS),Windows_NT)
	@where gh >NUL 2>&1 || (echo Error: gh CLI not found in PATH & exit /b 1)
else
	@if ! command -v gh >/dev/null 2>&1; then \
		echo "Error: gh CLI not found in PATH" >&2; \
		exit 1; \
	fi
endif
	@gh release list --repo aXedras/xScanner -L $(or $(LIMIT),20)

release-status:

ifeq ($(OS),Windows_NT)
	@where gh >NUL 2>&1 || (echo Error: gh CLI not found in PATH & exit /b 1)
	@echo "Latest GitHub release tag:"
	@powershell -NoProfile -Command "$$json = (gh release view --repo aXedras/xScanner --json tagName,publishedAt 2>$$null); if ($$LASTEXITCODE -ne 0 -or -not $$json) { Write-Output '  (none)'; exit 0 }; $$o = $$json | ConvertFrom-Json; $$published = $$o.publishedAt; if (-not $$published) { $$published = '' }; Write-Output ('  ' + $$o.tagName + ' (publishedAt=' + $$published + ')')"
	@echo.
	@echo Recent releases:
	@gh release list --repo aXedras/xScanner -L $(or $(LIMIT),20) || exit /b 1
else
	@if ! command -v gh >/dev/null 2>&1; then \
		echo "Error: gh CLI not found in PATH" >&2; \
		exit 1; \
	fi
	@echo "Latest GitHub release tag:"
	@if gh release view --repo aXedras/xScanner >/dev/null 2>&1; then \
		gh release view --repo aXedras/xScanner --json tagName,publishedAt --jq '"  " + .tagName + " (publishedAt=" + (.publishedAt // "") + ")"'; \
	else \
		echo "  (none)"; \
	fi
	@echo ""
	@echo "Recent releases:"
	@gh release list --repo aXedras/xScanner -L $(or $(LIMIT),20) || true
endif

version:

ifeq ($(OS),Windows_NT)
	@echo "Local repo:"
	@powershell -NoProfile -Command "$$b=(git branch --show-current); $$s=(git rev-parse --short HEAD); $$t=(git describe --tags --always 2>$$null); if(-not $$t){$$t='-'}; Write-Output ('  branch=' + $$b + ' sha=' + $$s + ' tag=' + $$t)"
	@powershell -NoProfile -Command "$$v=(& '$(VENV_PYTHON)' -c \"import tomllib;print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])\" 2>$$null); if(-not $$v){$$v='-'}; Write-Output ('  pyproject=' + $$v)"
	@echo ""
	@$(MAKE) release-status LIMIT=$(or $(LIMIT),20)
else
	@echo "Local repo:"
	@echo "  branch=$$(git branch --show-current) sha=$$(git rev-parse --short HEAD) tag=$$(git describe --tags --always 2>/dev/null || echo '-')"
	@echo "  pyproject=$$( \
		PY=python3; \
		if [ -x venv/bin/python ]; then PY=venv/bin/python; fi; \
		$$PY -c 'import tomllib;print(tomllib.load(open("pyproject.toml","rb"))["project"]["version"])' 2>/dev/null || echo '-' \
	)"
	@echo ""
	@$(MAKE) release-status LIMIT=$(or $(LIMIT),20)
endif

ci-main-status:
	@echo "Latest CI run on main:"
	@gh run list -R aXedras/xScanner -w "CI/CD Pipeline" -b main -L 1 || true


# Start all services (Supabase + FastAPI + Studio)
start-all: start-supabase

ifeq ($(OS),Windows_NT)
	@scripts\\windows\\development\\start-all.bat
else
	@echo "🚀 Starting all xScanner services..."
	@echo ""
	@echo "Supabase:"
	@if supabase status >/dev/null 2>&1; then \
		echo "   Status:           ✅ Running"; \
	fi
	@echo "   API:              $(SUPABASE_URL)"
	@echo "   Studio:           $(SUPABASE_STUDIO_URL)"
	@echo ""
	@echo "xScanner Server:"
	@echo "   API:              http://localhost:$(SERVER_PORT)"
	@echo "   Swagger Docs:     http://localhost:$(SERVER_PORT)/docs"
	@echo "   ReDoc:            http://localhost:$(SERVER_PORT)/redoc"
	@echo ""
	@echo "xScanner Studio:"
	@echo "   UI:               http://localhost:$(STUDIO_PORT)"
	@echo ""
	@make start-server & make start-studio
endif

# CLI Tools - Unified tool for testing and benchmarking
cli:
	@echo "🔧 xScanner CLI Tools"
	@echo ""
	@echo "📋 Available modes:"
	@echo ""
	@echo "  Interactive Testing:"
	@echo "    make cli-interactive         Interactive menu-driven test mode"
	@echo ""
	@echo "  Single Image Test:"
	@echo "    make cli-test IMAGE=path.jpg STRATEGY=chatgpt"
	@echo "    Available strategies: chatgpt, gemini, hybrid"
	@echo ""
	@echo "  List & Info:"
	@echo "    make cli-list-images         List all available test images"
	@echo "    make cli-list-strategies     List available strategies"
	@echo ""
	@echo "  Benchmarking:"
	@echo "    make cli-benchmark           Full benchmark + HTML report"
	@echo "    make cli-benchmark-quick     Quick benchmark (3 images) + HTML report"
	@echo ""
	@echo "  Report Generation:"
	@echo "    make cli-report              Generate current + missing history reports (reports/history/index.html)"
	@echo "    make cli-report-regenerate   Regenerate all history reports (reports/history/index.html)"
	@echo ""
	@echo "Examples:"
	@echo "  make cli-interactive"
	@echo "  make cli-test IMAGE=barPictures/gold.jpg STRATEGY=chatgpt"
	@echo "  make cli-benchmark-quick"
	@echo "  make cli-report"

cli-help: cli

cli-interactive:
	@$(VENV_PYTHON) -m tools.cli.cli --interactive

cli-test:
	$(if $(strip $(IMAGE)),,$(error IMAGE is required. Usage: make cli-test IMAGE=path.jpg STRATEGY=chatgpt))
	$(if $(strip $(STRATEGY)),,$(error STRATEGY is required. Usage: make cli-test IMAGE=path.jpg STRATEGY=chatgpt))
	@$(VENV_PYTHON) -m tools.cli.cli --image "$(IMAGE)" --strategy $(STRATEGY) -v

cli-list-images:
	@$(VENV_PYTHON) -m tools.cli.cli --list-images

cli-list-strategies:
	@$(VENV_PYTHON) -m tools.cli.cli --list-strategies

cli-benchmark:
	@echo "🔬 Running full benchmark + generating report..."
	@$(VENV_PYTHON) -m tools.cli.cli
	@echo ""
	@echo "📊 Generating HTML report..."
	@$(VENV_PYTHON) -m tools.cli.report
	@echo ""
	@echo "✅ Benchmark complete! View report at: reports/strategy_benchmark_report.html"

cli-benchmark-quick:
	@echo "⚡ Running quick benchmark (3 random images) + generating report..."
	@$(VENV_PYTHON) -m tools.cli.cli --quick
	@echo ""
	@echo "📊 Generating HTML report..."
	@$(VENV_PYTHON) -m tools.cli.report
	@echo ""
	@echo "✅ Quick benchmark complete! View report at: reports/strategy_benchmark_report.html"

cli-report:
	@echo "📊 Generating HTML reports..."
	@venv/bin/python -m tools.cli.report
	@echo ""
	@echo "✅ Reports generated!"
	@echo "   Current: reports/strategy_benchmark_report.html"
	@echo "   History: reports/history/index.html"

cli-report-history:
	@echo "🔄 Regenerating all history reports..."
	@venv/bin/python -m tools.cli.report --regenerate
	@echo ""
	@echo "✅ All reports regenerated!"
	@echo "   History: reports/history/index.html"

cli-report-regenerate: cli-report-history


# Build Docker image
docker-build:
	docker build -t bullion-bar-recognition:latest .

# Run Docker container
docker-run:
	docker run -p 8000:8000 \
		-e OPENAI_API_KEY=$(OPENAI_API_KEY) \
		-e AXEDRAS_USERNAME=$(AXEDRAS_USERNAME) \
		-e AXEDRAS_PASSWORD=$(AXEDRAS_PASSWORD) \
		bullion-bar-recognition:latest

# Clean generated files
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .mypy_cache .ruff_cache .pytest_cache
	rm -rf reports/
