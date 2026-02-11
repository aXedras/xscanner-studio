# xScanner Dockerfile
#
# Strategies: ChatGPT Vision, Gemini Flash, LoRA (external server)
# Final image: ~300MB (no heavy ML runtimes bundled)
#
# To build: docker build -t xscanner .

FROM python:3.11-slim

WORKDIR /app

# Install minimal system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy application code and runtime config
COPY src/ ./src/
COPY config/ ./config/
COPY pyproject.toml ./

# Install server + cloud dependencies (LoRA strategy uses core deps only)
RUN pip install --no-cache-dir -e ".[server,cloud]" && \
    pip cache purge

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Environment defaults
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/src \
    SERVER_HOST=0.0.0.0 \
    SERVER_PORT=8000 \
    SERVER_WORKERS=4

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Run server
CMD ["python", "-m", "xscanner.server.server"]
