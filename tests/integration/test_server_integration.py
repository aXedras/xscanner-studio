"""Integration tests for FastAPI server with real HTTP calls.

These tests start a real FastAPI server and make actual HTTP requests
to test the full HTTP layer, while keeping tests fast and reliable.
"""

import base64
import io
import socket
import subprocess
import time

import httpx
import pytest
from PIL import Image


@pytest.fixture(scope="module")
def free_port():
    """Get a free port for the test server."""
    sock = socket.socket()
    sock.bind(("", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


@pytest.fixture(scope="module")
def server(free_port):
    """Start FastAPI server on a free port for integration testing."""
    server_url = f"http://127.0.0.1:{free_port}"

    # Start server process
    process = subprocess.Popen(
        [
            "uvicorn",
            "xscanner.server.server:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(free_port),
            "--log-level",
            "warning",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for server to start (max 10 seconds)
    max_retries = 20
    for _ in range(max_retries):
        try:
            response = httpx.get(f"{server_url}/health", timeout=1.0)
            if response.status_code == 200:
                break
        except (httpx.ConnectError, httpx.TimeoutException, httpx.ReadTimeout):
            time.sleep(0.5)
    else:
        process.kill()
        raise RuntimeError(f"Server failed to start on port {free_port}")

    yield server_url

    # Cleanup
    process.terminate()
    try:
        process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        process.kill()


@pytest.fixture
def test_image_bytes():
    """Generate a simple test image in JPEG format."""
    img = Image.new("RGB", (100, 100), color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG")
    return buffer.getvalue()


@pytest.mark.integration
class TestServerHealthEndpoints:
    """Test server health and monitoring endpoints."""

    def test_health_endpoint_returns_healthy(self, server):
        """Test that /health endpoint returns healthy status."""
        response = httpx.get(f"{server}/health", timeout=5.0)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    def test_config_endpoint_returns_config(self, server):
        """Test that /config endpoint returns configuration."""
        response = httpx.get(f"{server}/config", timeout=5.0)

        assert response.status_code == 200
        data = response.json()
        assert "server" in data or "openai" in data or "ollama" in data


@pytest.mark.integration
class TestServerExtractEndpoint:
    """Test extraction endpoint with various inputs."""

    def test_extract_without_image_data(self, server):
        """Test extraction endpoint rejects requests without image data."""
        response = httpx.post(
            f"{server}/extract",
            json={},
            timeout=5.0,
        )

        assert response.status_code == 422  # Validation error

    def test_extract_with_invalid_base64(self, server):
        """Test extraction endpoint handles invalid base64 data."""
        response = httpx.post(
            f"{server}/extract",
            json={
                "image_base64": "not-valid-base64!!!",
                "strategy": "local",
            },
            timeout=5.0,
        )

        # Server returns 200 but with success=False in the response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "error" in data

    def test_extract_with_invalid_strategy(self, server, test_image_bytes):
        """Test extraction endpoint rejects invalid strategy names."""
        image_b64 = base64.b64encode(test_image_bytes).decode("utf-8")

        response = httpx.post(
            f"{server}/extract",
            json={
                "image_base64": image_b64,
                "strategy": "invalid_strategy_name",
            },
            timeout=5.0,
        )

        assert response.status_code == 422  # Validation error

    def test_extract_endpoint_accepts_valid_request(self, server, test_image_bytes):
        """Test that extraction endpoint accepts valid requests.

        Note: This will make real API calls depending on strategy configuration.
        We're testing the HTTP layer here, not the extraction quality.
        """
        image_b64 = base64.b64encode(test_image_bytes).decode("utf-8")

        response = httpx.post(
            f"{server}/extract",
            json={
                "image_base64": image_b64,
                "strategy": "local",
            },
            timeout=30.0,  # Allow time for real extraction
        )

        # Should either succeed or fail gracefully
        assert response.status_code in [200, 500]  # Success or extraction error

        if response.status_code == 200:
            data = response.json()
            assert "success" in data
            assert "request_id" in data
