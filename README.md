# xScanner

![CI/CD](https://github.com/aXedras/xScanner/workflows/CI/badge.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

**AI-powered bullion data extraction with Vision LLMs**

Extract serial numbers, metal type, weight, fineness, and producer information from precious metal bar images.

---

## 📚 Documentation

**Complete documentation is organized by component:**

### Server/Backend Documentation → [docs/](docs/)
Python FastAPI extraction service documentation.

- **[API Documentation](docs/API_DOCUMENTATION.md)** - REST API reference
- **[Testing Guide](docs/TESTING.md)** - Testing strategy
- **[Docker Deployment](docs/DOCKER.md)** - Container setup
- **[Contributing](docs/CONTRIBUTING.md)** - Development guidelines

### Studio/Frontend Documentation → [docs/studio/](docs/studio/)
React admin UI for extraction management.

- **[Studio Overview](docs/studio/README.md)** - Tech stack & workflow
- **[UI Architecture](docs/studio/UI_ARCHITECTURE.md)** - Components & routing
- **[Design System](docs/studio/DESIGN_SYSTEM.md)** - Brand colors & CSS classes

---

## 🚀 Quick Start

### Installation

```bash
git clone https://github.com/aXedras/xScanner.git
cd xScanner

# Install server
pip install -e ".[dev]"

# Install studio
cd studio && npm install

# Configure environment
cp .env.local.example .env.local  # Add API keys
```

### Run Server

```bash
# Start FastAPI server (port 8010)
make start-server

# Or with Python
python -m xscanner.server.server
```

Docs: http://localhost:8010/docs

### Run Studio

```bash
# Start all services (Supabase + Server + Studio)
make start-all

# Or studio only
make start-studio
```

Studio UI: http://localhost:8084

---

## 🎯 Key Features

### Server
- 🤖 Multiple extraction strategies (ChatGPT Vision, Gemini, PaddleOCR, Llama Vision)
- 🚀 REST API with FastAPI + OpenAPI docs
- 📊 Benchmarking & performance comparison
- 🐳 Docker support (Cloud ~300MB, Full ~3GB)
- 🧪 Comprehensive test suite

### Studio
- 🎨 Modern React + TypeScript UI
- 🔐 Supabase authentication & database
- 📦 Extraction management & editing
- 🖼️ Image storage & viewer
- ✨ xApp design system

---

## 🔧 Development

### Testing

```bash
# Unit tests (fast)
make test-unit

# Integration tests (mocked APIs, no API keys needed)
make test-integration

# Coverage report
make test-coverage
```

See [TESTING.md](docs/TESTING.md) for detailed testing guide.

### Code Quality

```bash
# Install pre-commit hooks (required for all contributors)
pre-commit install

# Run code quality checks
make lint
make format
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

```
xScanner/
├── src/xscanner/        # Server package
│   ├── server/          # FastAPI REST API
│   └── strategy/        # Extraction strategies
├── studio/              # React frontend
│   └── src/
│       ├── components/  # UI components
│       └── lib/         # Supabase client
├── docs/                # Server documentation
├── docs/studio/         # Studio documentation
├── tests/               # Test suite
└── supabase/            # Database migrations
```

See [docs/](docs/) and [docs/studio/](docs/studio/) for detailed documentation.

---

## 🤝 Contributing

1. Read [CONTRIBUTING.md](docs/CONTRIBUTING.md)
2. Install pre-commit hooks: `pre-commit install`
3. Run tests: `make test-unit`
4. Follow conventional commits

---

## 📄 License

MIT License

---

## 🔗 Links

- [GitHub Issues](https://github.com/aXedras/xScanner/issues)
- [API Docs](docs/API_DOCUMENTATION.md)
- [Changelog](docs/CHANGELOG.md)
