.PHONY: install dev format lint test test-unit test-integration test-coverage test-quick ci-local pre-commit-all server docker-build docker-run clean cli cli-test cli-list-images cli-list-strategies cli-run benchmark benchmark-help benchmark-full benchmark-report benchmark-quick

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

# CLI Tools - Interactive OCR testing
cli:
	@echo "📋 Available CLI commands:"
	@echo ""
	@echo "  make cli-test              Interactive OCR testing mode"
	@echo "  make cli-list-images       List available test images"
	@echo "  make cli-list-strategies   List available OCR strategies"
	@echo "  make cli-run               Run single test (requires IMAGE and STRATEGY)"
	@echo ""
	@echo "Examples:"
	@echo "  make cli-test"
	@echo "  make cli-run IMAGE=barPictures/gold.jpg STRATEGY=chatgpt"

cli-test:
	@python -m xscanner.cli.test

cli-list-images:
	@python -m xscanner.cli.test --list-images

cli-list-strategies:
	@python -m xscanner.cli.test --list-strategies

# Quick test (requires IMAGE and STRATEGY)
# Example: make cli-run IMAGE=path.jpg STRATEGY=chatgpt
cli-run:
	@python -m xscanner.cli.test --image "$(IMAGE)" --strategy $(STRATEGY)

# Benchmark - Compare all OCR strategies
benchmark-help:
	@echo "🔬 Available Benchmark commands:"
	@echo ""
	@echo "  make benchmark             Run full benchmark + generate report"
	@echo "  make benchmark-full        Run full benchmark (all images)"
	@echo "  make benchmark-quick       Quick benchmark (3 random images)"
	@echo "  make benchmark-report      Generate HTML report from results"
	@echo ""
	@echo "Examples:"
	@echo "  make benchmark-quick       # Fast test with 3 images"
	@echo "  make benchmark             # Full suite with report"

benchmark:
	@echo "🔬 Running full benchmark suite..."
	@python -m xscanner.benchmark.comparator
	@echo ""
	@echo "📊 Generating HTML report..."
	@python -m xscanner.benchmark.report
	@echo ""
	@echo "✅ Benchmark complete! View report at: reports/strategy_benchmark_report.html"

benchmark-full:
	@python -m xscanner.benchmark.comparator

benchmark-quick:
	@python -m xscanner.benchmark.comparator --quick

benchmark-report:
	@python -m xscanner.benchmark.report

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
