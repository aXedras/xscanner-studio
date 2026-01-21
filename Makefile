.PHONY: install dev format lint test test-all test-unit test-integration test-e2e test-coverage test-quick ci-local pre-commit-all server docker-build docker-run clean cli cli-help cli-interactive cli-test cli-list-images cli-list-strategies cli-benchmark cli-benchmark-quick cli-report cli-report-history

# Install production dependencies
install:
	pip install -e .

# Install with server dependencies
install-server:
	pip install -e ".[server]"

# Install development dependencies
dev:
	pip install -e ".[dev]"
	pre-commit install

# Format code
format:
	ruff format .
	ruff check --fix .

# Lint code (no fixes)
lint:
	ruff check .
	ruff format --check .
	mypy src/xscanner/ --ignore-missing-imports

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
	pytest tests/ -v

# Run only fast unit tests
test-unit:
	@echo "⚡ Running unit tests only..."
	pytest tests/unit/ -v

# Run only integration tests
test-integration:
	@echo "🔌 Running integration tests (mocked APIs, no API keys needed)..."
	pytest tests/integration/ -v -m integration

# Run only e2e tests
test-e2e:
	@echo "🚀 Running e2e tests (requires API keys & services)..."
	pytest tests/e2e/ -v -m e2e

# Run tests with coverage report
test-coverage:
	@echo "📊 Running tests with coverage..."
	pytest tests/ --cov=src/xscanner --cov-report=html --cov-report=term
	@echo ""
	@echo "✅ Coverage report generated: htmlcov/index.html"

# Run quick tests (unit only, for pre-commit)
test-quick:
	@echo "⚡ Running quick tests..."
	pytest tests/unit/ -q

# Run server locally
server:
	@bash scripts/start-server.sh $(PORT)

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
