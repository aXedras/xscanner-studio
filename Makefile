.PHONY: help install dev format lint test test-all test-unit test-integration test-e2e test-coverage test-quick ci-local pre-commit-all db-types db-types-generate db-types-check database database-start database-stop start start-server start-studio start-supabase start-all preprod preprod-check preprod-update-main preprod-up preprod-down preprod-health preprod-status preprod-logs preprod-deploy release release-help release-create release-status release-list version ci-main-status docker-build docker-run clean cli cli-help cli-interactive cli-test cli-list-images cli-list-strategies cli-benchmark cli-benchmark-quick cli-report cli-report-history

# Load environment variables from .env.local
-include .env.local
export

# Extract Studio port from vite.config.ts
STUDIO_PORT := $(shell grep -oP 'port:\s*\K\d+' studio/vite.config.ts 2>/dev/null || echo 8084)

# Install production dependencies
install:
	pip install -e .

# Show an overview of the most important commands
help:
	@echo "xScanner Make Targets"
	@echo "  make start     # dev services help"
	@echo "  make database  # Supabase start/stop help"
	@echo "  make preprod   # pre-prod deploy help"
	@echo "  make release   # release help"
	@echo "  make version   # show local version + latest GitHub release"
	@echo "  make test      # test targets help"
	@echo "  make cli       # CLI help"
	@echo "  make db-types  # DB types help"

# Install with server dependencies
install-server:
	pip install -e ".[server]"

# Install development dependencies
dev:
	pip install -e ".[dev]"
	pre-commit install

# Format code
format:
	@venv/bin/ruff format .
	@venv/bin/ruff check --fix .

# Lint code (no fixes)
lint: db-types-check
	@venv/bin/ruff check .
	@venv/bin/ruff format --check .
	@venv/bin/mypy src/xscanner/ --ignore-missing-imports

# DB types (server)
db-types:
	@echo "🧬 Server DB Types"
	@echo ""
	@echo "  make db-types-generate   Generate src/xscanner/server/db_types.py"
	@echo "  make db-types-check      Verify DB types match supabase/migrations"

db-types-generate:
	@venv/bin/python -m scripts.db.gen_db_types

db-types-check:
	@venv/bin/python -m scripts.db.check_db_types

# Run ALL CI checks locally (exactly what CI runs)
ci-local: lint test
	@echo "✅ All CI checks passed locally!"

# Run pre-commit on all files (what pre-commit hook does)
pre-commit-all:
	pre-commit run --all-files

# Run tests
test:
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
	@venv/bin/python -m pytest tests/ -v

# Run only fast unit tests
test-unit:
	@echo "⚡ Running unit tests only..."
	@venv/bin/python -m pytest tests/unit/ -v

# Run only integration tests
test-integration:
	@echo "🔌 Running integration tests (mocked APIs, no API keys needed)..."
	@venv/bin/python -m pytest tests/integration/ -v -m integration

# Run only e2e tests
test-e2e:
	@echo "🚀 Running e2e tests (requires API keys & services)..."
	@venv/bin/python -m pytest tests/e2e/ -v -m e2e

# Run tests with coverage report
test-coverage:
	@echo "📊 Running tests with coverage..."
	@venv/bin/python -m pytest tests/ --cov=src/xscanner --cov-report=html --cov-report=term
	@echo ""
	@echo "✅ Coverage report generated: htmlcov/index.html"

# Run quick tests (unit only, for pre-commit)
test-quick:
	@echo "⚡ Running quick tests..."
	@venv/bin/python -m pytest tests/unit/ -q

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

# Start FastAPI backend
start-server:
	@bash scripts/development/start-server.sh

# Start Vite studio UI
start-studio:
	@cd studio && npm run dev

# Start or check Supabase
start-supabase:
	@make database-start

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
	@bash scripts/preprod/database-start.sh

database-stop:
	@bash scripts/preprod/database-stop.sh

# Pre-prod deployment commands
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
	@bash scripts/preprod/check.sh

preprod-update-main:
	@bash scripts/preprod/update-main.sh

preprod-up:
	@bash scripts/preprod/database-start.sh
	@bash scripts/preprod/up.sh

preprod-down:
	@bash scripts/preprod/down.sh

preprod-health:
	@bash scripts/preprod/health.sh

preprod-status:
	@bash scripts/preprod/status.sh

preprod-logs:
	@bash scripts/preprod/logs.sh

preprod-deploy:
	@bash scripts/preprod/deploy.sh

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
	@if [ -z "$(VERSION)" ]; then \
		echo "Error: VERSION is required" >&2; \
		echo "Usage: make release-create VERSION=X.Y.Z" >&2; \
		exit 1; \
	fi
	@VERSION="$(VERSION)" bash scripts/release/create-release.sh

release-list:
	@if ! command -v gh >/dev/null 2>&1; then \
		echo "Error: gh CLI not found in PATH" >&2; \
		exit 1; \
	fi
	@gh release list --repo aXedras/xScanner -L $(or $(LIMIT),20)

release-status:
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

version:
	@echo "Local repo:"
	@echo "  branch=$$(git branch --show-current) sha=$$(git rev-parse --short HEAD) tag=$$(git describe --tags --always 2>/dev/null || echo '-')"
	@echo "  pyproject=$$( \
		PY=python3; \
		if [ -x venv/bin/python ]; then PY=venv/bin/python; fi; \
		$$PY -c 'import tomllib;print(tomllib.load(open("pyproject.toml","rb"))["project"]["version"])' 2>/dev/null || echo '-' \
	)"
	@echo ""
	@$(MAKE) release-status LIMIT=$(or $(LIMIT),20)

ci-main-status:
	@echo "Latest CI run on main:"
	@gh run list -R aXedras/xScanner -w "CI/CD Pipeline" -b main -L 1 || true


# Start all services (Supabase + FastAPI + Studio)
start-all: start-supabase
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
	@venv/bin/python -m tools.cli.cli --interactive

cli-test:
	@if [ -z "$(IMAGE)" ] || [ -z "$(STRATEGY)" ]; then \
		echo "Error: IMAGE and STRATEGY are required" >&2; \
		echo "Usage: make cli-test IMAGE=path.jpg STRATEGY=chatgpt" >&2; \
		exit 1; \
	fi
	@venv/bin/python -m tools.cli.cli --image "$(IMAGE)" --strategy $(STRATEGY) -v

cli-list-images:
	@venv/bin/python -m tools.cli.cli --list-images

cli-list-strategies:
	@venv/bin/python -m tools.cli.cli --list-strategies

cli-benchmark:
	@echo "🔬 Running full benchmark + generating report..."
	@venv/bin/python -m tools.cli.cli
	@echo ""
	@echo "📊 Generating HTML report..."
	@venv/bin/python -m tools.cli.report
	@echo ""
	@echo "✅ Benchmark complete! View report at: reports/strategy_benchmark_report.html"

cli-benchmark-quick:
	@echo "⚡ Running quick benchmark (3 random images) + generating report..."
	@venv/bin/python -m tools.cli.cli --quick
	@echo ""
	@echo "📊 Generating HTML report..."
	@venv/bin/python -m tools.cli.report
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
