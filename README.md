# xScanner

![CI/CD](https://github.com/aXedras/xScanner/workflows/CI/badge.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

**AI-powered OCR and Vision API for extracting structured data from bullion bar images**

Extract serial numbers, metal type, weight, fineness, and producer information from gold, silver, platinum, and palladium bar images using state-of-the-art OCR and Vision LLM technologies.

## 📚 Documentation

- **[API Documentation](docs/API_DOCUMENTATION.md)** - Complete REST API reference
- **[Testing Guide](docs/TESTING.md)** - Testing strategy and conventions
- **[Docker Deployment](docs/DOCKER.md)** - Container setup and deployment
- **[Pre-commit Setup](docs/PRE_COMMIT_SETUP.md)** - Code quality enforcement
- **[Development Backlog](docs/BACKLOG.md)** - Feature roadmap and technical debt
- **[Contributing Guidelines](docs/CONTRIBUTING.md)** - How to contribute to the project
- **[Changelog](docs/CHANGELOG.md)** - Version history and release notes

## 🎯 Overview

REST API and CLI tools for automated extraction of metadata from precious metal bar images. Combines traditional OCR with Vision Language Models for high accuracy.

### Key Features

- 🤖 **Multiple OCR Strategies**: ChatGPT Vision, Gemini Flash, PaddleOCR, Llama Vision, Hybrid
- 🚀 **REST API**: FastAPI with async support and OpenAPI documentation
- 📊 **Performance Benchmarking**: Compare strategies with visual reports
- 🐳 **Docker Support**: Cloud (~300MB) and Full (~3GB) images - see [DOCKER.md](docs/DOCKER.md)
- 🔄 **CI/CD Pipeline**: Automated testing, linting, and Docker builds
- 🧪 **Comprehensive Testing**: 49 unit tests, integration tests - see [TESTING.md](docs/TESTING.md)

### Architecture

**Stateless Design**: No database, images processed on-demand, horizontal scalability
**Python Stack**: FastAPI, PaddleOCR, OpenCV, OpenAI/Google APIs
**Local LLM**: Ollama/Llama 3.2 Vision for privacy-focused deployments

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- (Optional) Ollama for local LLM inference
- (Optional) Docker for containerized deployment

### Installation

```bash
# Clone repository
git clone https://github.com/aXedras/xScanner.git
cd xScanner

# Install as package (recommended - new structure)
pip install -e ".[dev]"

# Or install from requirements files
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Configure API keys (create .env.local file)
# See docs/API_DOCUMENTATION.md for details
```

### Running the Server

```bash
# Using Python module (recommended)
python -m xscanner.server.server

# Development tools (outside package)
python -m tools.cli.test --list-strategies
python -m tools.benchmark.comparator --quick

# Or with uvicorn
uvicorn xscanner.server.server:app --reload

# Or with Make
make run
```

Server: `http://localhost:8000` | Docs: `http://localhost:8000/docs`

### Quick API Example

See [API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md) for complete reference.

```bash
# Extract from uploaded image
curl -X POST "http://localhost:8000/extract/upload" \
  -F "file=@bullion_bar.jpg" \
  -F "strategy=cloud"
```

---

## 📊 Testing & Benchmarking

```bash
# Unit tests (fast, no external dependencies)
make test-unit

# Integration tests (requires API keys)
make test-integration

# Coverage report
make test-coverage

# OCR strategy comparison
python tests/integration/test_ocr_strategies.py
```

See [TESTING.md](docs/TESTING.md) for detailed testing guide.

---

## 🔧 Development

### Code Quality

```bash
# Install pre-commit hooks (required for all contributors)
pre-commit install

# Run code quality checks
make lint
make format
make typecheck
```

See [PRE_COMMIT_SETUP.md](docs/PRE_COMMIT_SETUP.md) for details on hooks and enforcement.

### CI/CD Pipeline

GitHub Actions runs on every push/PR:
- **Lint**: Ruff linter + formatter, Mypy type checking
- **Test**: Pytest with coverage reporting
- **Build**: Docker images → GitHub Container Registry

See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for branch naming and commit conventions.

---

## 🐳 Docker Deployment

Two image variants available:
- **Cloud** (~300MB): ChatGPT + Gemini only
- **Full** (~3GB): All strategies including PaddleOCR + Llama Vision

```bash
# Pull and run cloud image
docker pull ghcr.io/axedras/xscanner:latest
docker run -p 8000:8000 -e OPENAI_API_KEY=sk-... ghcr.io/axedras/xscanner:latest
```

See [DOCKER.md](docs/DOCKER.md) for complete deployment guide.

---

## 📁 Project Structure

**New Package Structure** (v1.1.0+):

```
xScanner/
├── src/xscanner/                 # Main package (installable)
│   ├── server/                   # FastAPI server & services
│   │   ├── server.py             # REST API endpoints
│   │   ├── config.py             # Configuration management
│   │   ├── extraction.py         # Extraction service
│   │   └── axedras_client.py     # BIL integration
│   ├── strategy/                 # OCR strategies
│   │   ├── base.py               # Strategy interface
│   │   ├── chatgpt_vision_strategy.py
│   │   ├── gemini_flash_strategy.py
│   │   ├── paddleocr_strategy.py
│   │   ├── ollama_vision_strategy.py
│   │   ├── paddle_llama_hybrid_strategy.py
│   │   └── parser.py             # Data parser
├── tools/                        # Development tools (not installed)
│   ├── cli/                      # CLI testing tools
│   │   └── test.py               # Interactive OCR testing
│   └── benchmark/                # Performance benchmarks
│       ├── comparator.py         # Strategy comparison
│       └── report.py             # HTML report generator
├── tests/                        # Test suite
│   ├── unit/                     # Unit tests (49 tests)
│   ├── integration/              # Integration tests
│   └── conftest.py               # Pytest fixtures
├── docs/                         # Documentation
├── config/                       # Prompt templates
├── scripts/                      # Utility scripts
└── pyproject.toml                # Package configuration
```

---

## 🔑 Configuration

Create `.env.local` file for API keys:

```bash
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...
OLLAMA_BASE_URL=http://localhost:11434
```

See [API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md) for all configuration options.

---

## 🤝 Contributing

See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

Quick start:
```bash
# 1. Fork and clone
# 2. Install dependencies
pip install -e ".[dev]"

# 3. Install pre-commit hooks (required!)
pre-commit install

# 4. Create feature branch
git checkout -b feature/my-feature

# 5. Make changes, run tests
make test-unit

# 6. Commit with conventional commits
git commit -m "feat: add my feature"
```

---

## 📄 License

MIT License - See LICENSE file for details

---

## 📞 Support & Links

- **Issues**: [GitHub Issues](https://github.com/aXedras/xScanner/issues)
- **Related**: [aXedras Bullion Integrity Ledger](https://github.com/aXedras/BIL)
