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

## �️ CLI Tools

Quick command-line tools for direct API testing without running the full server.

### LoRA Analysis Tool

Analyze images using the fine-tuned LoRA model on RunPod:

```bash
# Basic usage with default prompts
./tools/lora_analyze.sh barPictures/Renamed-and-Sorted/Gold_01000g_9999_AR95742_Valcambi.jpg

# Verbose output
./tools/lora_analyze.sh barPictures/my_bar.jpg -v

# Custom prompts
./tools/lora_analyze.sh barPictures/my_bar.jpg \
  -s config/lora_system_prompt.txt \
  -p config/lora_user_prompt.txt

# Without prompts (use server defaults)
./tools/lora_analyze.sh barPictures/my_bar.jpg --no-prompts

# Custom server URL
LORA_BASE_URL=http://localhost:8000 ./tools/lora_analyze.sh barPictures/my_bar.jpg
```

**Options:**
- `-u, --url URL` - LoRA server URL (default: RunPod endpoint)
- `-s, --system-prompt FILE` - System prompt file
- `-p, --user-prompt FILE` - User prompt file
- `--no-prompts` - Don't send prompts
- `-r, --raw` - Raw JSON output
- `-v, --verbose` - Verbose mode

### ChatGPT Vision Tool

Analyze images using OpenAI GPT-4o Vision API:

```bash
# Requires OPENAI_API_KEY environment variable
export OPENAI_API_KEY=sk-...

# Basic usage with gpt-4o-mini
./tools/chatgpt_analyze.sh barPictures/Renamed-and-Sorted/Gold_01000g_9999_AR95742_Valcambi.jpg

# Use GPT-4o for better accuracy
./tools/chatgpt_analyze.sh barPictures/my_bar.jpg --model gpt-4o

# Verbose with token statistics
./tools/chatgpt_analyze.sh barPictures/my_bar.jpg -v

# Custom prompts
./tools/chatgpt_analyze.sh barPictures/my_bar.jpg \
  -s config/system_prompt_image.txt \
  -p config/prompt_template_image.txt
```

**Options:**
- `-m, --model MODEL` - Model: `gpt-4o-mini`, `gpt-4o`, `gpt-4-turbo`
- `-s, --system-prompt FILE` - System prompt file
- `-p, --user-prompt FILE` - User prompt file
- `-t, --temperature TEMP` - Temperature (default: 0.1)
- `--max-tokens TOKENS` - Max output tokens (default: 1200)
- `-r, --raw` - Raw JSON output
- `-v, --verbose` - Verbose mode with token stats

---

## �🔧 Development

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
