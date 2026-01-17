"""Integration tests for FastAPI server with real HTTP calls.

These tests start a real FastAPI server and make actual HTTP requests
to test the full HTTP layer, while keeping tests fast and reliable.
"""

import base64
import io
import socket
import subprocess
import sys
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
            sys.executable,
            "-m",
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

    def test_extract_with_mock_mode(self, server, test_image_bytes):
        """Test extraction endpoint with mock mode enabled (local=Hybrid)."""
        image_b64 = base64.b64encode(test_image_bytes).decode("utf-8")

        response = httpx.post(
            f"{server}/extract",
            json={
                "image_base64": image_b64,
                "strategy": "local",
                "use_mock": True,
            },
            timeout=5.0,
        )

        assert response.status_code == 200
        data = response.json()
        # Success can be True or False depending on random mock data (may include errors)
        assert "success" in data
        # Strategy should be Hybrid-related for local
        assert (
            "Hybrid" in data["strategy_used"]
            or "Ollama" in data["strategy_used"]
            or "Paddle" in data["strategy_used"]
        )
        assert "(mock)" in data["strategy_used"]
        assert "structured_data" in data
        assert "request_id" in data

    def test_extract_upload_with_mock_mode(self, server, test_image_bytes):
        """Test /extract/upload endpoint with mock mode enabled (cloud=ChatGPT/Gemini)."""
        response = httpx.post(
            f"{server}/extract/upload",
            files={"file": ("test.jpg", test_image_bytes, "image/jpeg")},
            data={
                "strategy": "cloud",
                "use_mock": "true",
            },
            timeout=5.0,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # Strategy should be ChatGPT or Gemini for cloud
        assert "ChatGPT" in data["strategy_used"] or "Gemini" in data["strategy_used"]
        assert "(mock)" in data["strategy_used"]
        assert "structured_data" in data
        assert "request_id" in data
        assert data["processing_time"] > 0

    def test_extract_endpoint_accepts_valid_request(self, server, test_image_bytes):
        """Test that extraction endpoint accepts valid requests with strategy-specific mocks.

        Note: This uses mock mode to avoid dependency on external services.
        Mock data comes from real benchmark results, including potential error cases.
        """
        image_b64 = base64.b64encode(test_image_bytes).decode("utf-8")

        response = httpx.post(
            f"{server}/extract",
            json={
                "image_base64": image_b64,
                "strategy": "local",
                "use_mock": True,
            },
            timeout=5.0,  # Mock strategy should be fast
        )

        # Mock strategy should return a response
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert (
            "Hybrid" in data["strategy_used"]
            or "Ollama" in data["strategy_used"]
            or "Paddle" in data["strategy_used"]
        )
        assert "structured_data" in data
        assert "request_id" in data


@pytest.mark.integration
class TestServerUploadEndpointStrategy:
    """Test /extract/upload endpoint strategy parameter handling."""

    def test_upload_strategy_parameter_local(self, server, test_image_bytes):
        """Test that strategy='local' works with file upload."""
        response = httpx.post(
            f"{server}/extract/upload",
            files={"file": ("test.jpg", test_image_bytes, "image/jpeg")},
            data={
                "strategy": "local",
                "use_mock": "true",
            },
            timeout=5.0,
        )

        assert response.status_code == 200
        data = response.json()
        assert (
            "Hybrid" in data["strategy_used"]
            or "Ollama" in data["strategy_used"]
            or "Paddle" in data["strategy_used"]
        ), f"Expected local strategy, got: {data['strategy_used']}"

    def test_upload_strategy_parameter_cloud(self, server, test_image_bytes):
        """Test that strategy='cloud' works with file upload."""
        response = httpx.post(
            f"{server}/extract/upload",
            files={"file": ("test.jpg", test_image_bytes, "image/jpeg")},
            data={
                "strategy": "cloud",
                "use_mock": "true",
            },
            timeout=5.0,
        )

        assert response.status_code == 200
        data = response.json()
        assert "ChatGPT" in data["strategy_used"] or "Gemini" in data["strategy_used"], (
            f"Expected cloud strategy, got: {data['strategy_used']}"
        )

    def test_upload_strategy_parameter_default(self, server, test_image_bytes):
        """Test that default strategy works with file upload (defaults to cloud)."""
        response = httpx.post(
            f"{server}/extract/upload",
            files={"file": ("test.jpg", test_image_bytes, "image/jpeg")},
            data={
                "use_mock": "true",
                # No strategy parameter - defaults to cloud
            },
            timeout=5.0,
        )

        assert response.status_code == 200
        data = response.json()
        # Default is cloud (consistent with /extract endpoint)
        assert "ChatGPT" in data["strategy_used"] or "Gemini" in data["strategy_used"], (
            f"Expected default cloud strategy, got: {data['strategy_used']}"
        )

    def test_strategy_parameter_local(self, server, test_image_bytes):
        """Test that strategy='local' uses Hybrid/Ollama strategy."""
        image_b64 = base64.b64encode(test_image_bytes).decode("utf-8")

        response = httpx.post(
            f"{server}/extract",
            json={
                "image_base64": image_b64,
                "strategy": "local",
                "use_mock": True,
            },
            timeout=5.0,
        )

        assert response.status_code == 200
        data = response.json()
        # Verify correct strategy was used
        assert (
            "Hybrid" in data["strategy_used"]
            or "Ollama" in data["strategy_used"]
            or "Paddle" in data["strategy_used"]
        ), f"Expected local strategy, got: {data['strategy_used']}"

    def test_strategy_parameter_cloud(self, server, test_image_bytes):
        """Test that strategy='cloud' uses ChatGPT/Gemini strategy."""
        image_b64 = base64.b64encode(test_image_bytes).decode("utf-8")

        response = httpx.post(
            f"{server}/extract",
            json={
                "image_base64": image_b64,
                "strategy": "cloud",
                "use_mock": True,
            },
            timeout=5.0,
        )

        assert response.status_code == 200
        data = response.json()
        # Verify correct strategy was used
        assert "ChatGPT" in data["strategy_used"] or "Gemini" in data["strategy_used"], (
            f"Expected cloud strategy, got: {data['strategy_used']}"
        )

    def test_strategy_parameter_default(self, server, test_image_bytes):
        """Test that default strategy (no parameter) uses cloud."""
        image_b64 = base64.b64encode(test_image_bytes).decode("utf-8")

        response = httpx.post(
            f"{server}/extract",
            json={
                "image_base64": image_b64,
                "use_mock": True,
                # No strategy parameter - should default to cloud
            },
            timeout=5.0,
        )

        assert response.status_code == 200
        data = response.json()
        # Default should be cloud (ChatGPT/Gemini)
        assert "ChatGPT" in data["strategy_used"] or "Gemini" in data["strategy_used"], (
            f"Expected default to cloud strategy, got: {data['strategy_used']}"
        )

    def test_strategy_parameter_case_sensitive(self, server, test_image_bytes):
        """Test that strategy parameter is case-sensitive (only lowercase accepted)."""
        image_b64 = base64.b64encode(test_image_bytes).decode("utf-8")

        # Test uppercase - should be rejected
        response = httpx.post(
            f"{server}/extract",
            json={
                "image_base64": image_b64,
                "strategy": "CLOUD",
                "use_mock": True,
            },
            timeout=5.0,
        )

        assert response.status_code == 422  # Validation error - invalid enum value

        # Test mixed case - should be rejected
        response = httpx.post(
            f"{server}/extract",
            json={
                "image_base64": image_b64,
                "strategy": "Local",
                "use_mock": True,
            },
            timeout=5.0,
        )

        assert response.status_code == 422  # Validation error - invalid enum value

        # Test lowercase - should work
        response = httpx.post(
            f"{server}/extract",
            json={
                "image_base64": image_b64,
                "strategy": "local",
                "use_mock": True,
            },
            timeout=5.0,
        )

        assert response.status_code == 200
        data = response.json()
        assert (
            "Hybrid" in data["strategy_used"]
            or "Ollama" in data["strategy_used"]
            or "Paddle" in data["strategy_used"]
        )
