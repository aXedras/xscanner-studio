.PHONY: install dev format lint test test-unit test-integration test-coverage test-quick ci-local pre-commit-all server docker-build docker-run clean cli cli-help cli-interactive cli-test cli-list-images cli-list-strategies cli-benchmark cli-benchmark-quick

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
	@echo "🧪 Running all tests (unit + integration)..."
	pytest tests/ -v

# Run only fast unit tests
test-unit:
	@echo "⚡ Running unit tests only..."
	pytest tests/unit/ -v

# Run only integration tests
test-integration:
	@echo "🔌 Running integration tests (requires API keys)..."
	pytest tests/integration/ -v -m integration

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
	@echo "Examples:"
	@echo "  make cli-interactive"
	@echo "  make cli-test IMAGE=barPictures/gold.jpg STRATEGY=chatgpt"
	@echo "  make cli-benchmark-quick"

cli-help: cli

cli-interactive:
	@python -m tools.cli.cli --interactive

cli-test:
	@python -m tools.cli.cli --image "$(IMAGE)" --strategy $(STRATEGY) -v

cli-list-images:
	@python -m tools.cli.cli --list-images

cli-list-strategies:
	@python -m tools.cli.cli --list-strategies

cli-benchmark:
	@echo "🔬 Running full benchmark + generating report..."
	@python -m tools.cli.cli
	@echo ""
	@echo "📊 Generating HTML report..."
	@python -m tools.cli.report
	@echo ""
	@echo "✅ Benchmark complete! View report at: reports/strategy_benchmark_report.html"

cli-benchmark-quick:
	@echo "⚡ Running quick benchmark (3 random images) + generating report..."
	@python -m tools.cli.cli --quick
	@echo ""
	@echo "📊 Generating HTML report..."
	@python -m tools.cli.report
	@echo ""
	@echo "✅ Quick benchmark complete! View report at: reports/strategy_benchmark_report.html"



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
