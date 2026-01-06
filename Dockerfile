# Default xScanner Dockerfile - Cloud APIs Only (Lightweight)
# For full version with PaddleOCR, see Dockerfile.full
# For cloud-only lightweight version, see Dockerfile.cloud (this is it!)
#
# This is the RECOMMENDED production image:
# - Only ChatGPT Vision + Gemini Flash strategies
# - Final image: ~300MB
# - Fast startup, low memory footprint
# - Perfect for cloud deployment
#
# To build: docker build -t xscanner:cloud .
# To build full version: docker build -f Dockerfile.full -t xscanner:full .

FROM python:3.11-slim

WORKDIR /app

# Install minimal system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy application code
COPY src/ ./src/
COPY ocr_strategies/ ./ocr_strategies/
COPY config/prompt_template_image.txt config/system_prompt_image.txt ./config/
COPY pyproject.toml ./

# Install only cloud dependencies (no ML libraries!)
RUN pip install --no-cache-dir -e ".[server,cloud]" && \
    pip cache purge

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Environment defaults
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    SERVER_HOST=0.0.0.0 \
    SERVER_PORT=8000 \
    SERVER_WORKERS=4

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Run server
CMD ["python", "-m", "src.server"]
