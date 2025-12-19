.PHONY: install dev format lint test server docker-build docker-run clean

# Install production dependencies
install:
	pip install -r requirements.txt -r requirements-server.txt

# Install development dependencies
dev:
	pip install -r requirements.txt -r requirements-server.txt -r requirements-dev.txt
	pre-commit install

# Format code
format:
	ruff format .
	ruff check --fix .

# Lint code (no fixes)
lint:
	ruff check .
	ruff format --check .
	mypy src/ ocr_strategies/ --ignore-missing-imports

# Run tests
test:
	pytest tests/ -v

# Run server locally
server:
	python -m src.server

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
	rm -rf reports/ ocr_comparison_results.json
