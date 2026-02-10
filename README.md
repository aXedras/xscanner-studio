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

Analyze images using OpenAI GPT-5.2 Vision API:

```bash
# Requires OPENAI_API_KEY environment variable
export OPENAI_API_KEY=sk-...

# Basic usage with gpt-5.2
./tools/chatgpt_analyze.sh barPictures/Renamed-and-Sorted/Gold_01000g_9999_AR95742_Valcambi.jpg

# Use GPT-5.2 for better accuracy
./tools/chatgpt_analyze.sh barPictures/my_bar.jpg --model gpt-5.2

# Verbose with token statistics
./tools/chatgpt_analyze.sh barPictures/my_bar.jpg -v

# Custom prompts
./tools/chatgpt_analyze.sh barPictures/my_bar.jpg \
  -s config/system_prompt_image.txt \
  -p config/prompt_template_image.txt
```

**Options:**
- `-m, --model MODEL` - Model: `gpt-5.2`
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

## Testing

LoRA direkt auf RundPod:
<code>
curl -X POST https://ln5k5kxgyy3sqz-8000.proxy.runpod.net/analyze \
  -F "image=@/Users/marcopersi/development/xScanner/tests/fixtures/images/bars/Gold_00500g_9999_A55251_Heraeus.jpg"
</code>

LoRA auf xScanner:
<code>
curl -X POST http://localhost:8000/extract/upload \
  -F "file=@/Users/marcopersi/development/xScanner/tests/fixtures/images/bars/Gold_00500g_9999_A55251_Heraeus.jpg" \
  -F "strategy=local" \
  -F "register_on_bil=false"
</code>


## Benchmarking

```bash
# Activate venv first
source venv/bin/activate

# Full benchmark (all images, all strategies)
python -m cli

# Quick benchmark (3 random images)
python -m cli --quick

# Sample benchmark with specific strategies
python -m cli --sample-size 25 --strategies lora,lora-2stage,lora-2stage-v2

# Only LoRA strategies
python -m cli --strategies lora,lora-2stage,lora-2stage-v2

# Only ChatGPT strategies
python -m cli --strategies chatgpt-2stage,chatgpt-2stage-v2

# Test single image
python -m cli --image barPictures/my_bar.jpg --strategy lora

# Interactive mode
python -m cli --interactive

# List available images/strategies
python -m cli --list-images
python -m cli --list-strategies
```

**Benchmark Options:**
- `--sample-size N` - Random sample of N images (troyounce images always included)
- `--quick` - Quick test with 3 random images
- `--strategies LIST` - Comma-separated: `lora,lora-2stage,lora-2stage-v2,chatgpt-2stage,chatgpt-2stage-v2`
- `--difficult-only` - Only test on barPictures/difficult folder
- `--workers N` - Parallel strategy workers per image
- `--image-workers N` - Parallel image processing

---

## 🔐 Environment Files

| File | Purpose | Used By |
|------|---------|--------|
| `.env.example` | Template with all config keys | Copy to `.env.local` for local dev |
| `.env.local` | Local development (secrets) | Server auto-loads, **gitignored** |
| `.env.ci` | CI/CD (no secrets) | GitHub Actions via `$GITHUB_ENV` |
| `.env.preprod.example` | Pre-prod Docker template | Copy to `.env.preprod` |
| `studio/.env.example` | Studio (Vite) template | Copy to `studio/.env.local` |

**Key categories:**
- **Providers**: `OPENAI_API_KEY`, `GOOGLE_API_KEY`, `LORA_BASE_URL`
- **Prompts**: `LORA_*_PROMPT_FILE`, `CHATGPT_*_PROMPT_FILE`
- **Server**: `SERVER_HOST`, `SERVER_PORT`
- **Persistence**: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`
- **Logging**: `LOG_LEVEL`, `LOG_FILE`

---

## 📄 License

MIT License

---

## 🔗 Links

- [GitHub Issues](https://github.com/aXedras/xScanner/issues)
- [API Docs](docs/API_DOCUMENTATION.md)
- [Changelog](docs/CHANGELOG.md)
