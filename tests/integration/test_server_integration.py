"""Integration tests for FastAPI server with real HTTP calls.

These tests start a real FastAPI server and make actual HTTP requests
to test the full HTTP layer, while keeping tests fast and reliable.
"""

import base64
import io
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest
from PIL import Image

from tools.cli.validator import parse_filename_ground_truth, validate_extraction

# Get project root for PYTHONPATH
PROJECT_ROOT = Path(__file__).parent.parent.parent


def _remove_supabase_env(env: dict[str, str]) -> dict[str, str]:
    """Return a copy of env with all SUPABASE_* vars removed.

    Integration tests should not depend on Supabase persistence.
    """

    cleaned = dict(env)
    for key in list(cleaned.keys()):
        if key.startswith("SUPABASE_"):
            cleaned.pop(key, None)

    # Prevent python-dotenv from loading Supabase credentials from .env.local.
    # load_dotenv(..., override=False) still sets variables that are missing.
    cleaned["SUPABASE_URL"] = ""
    cleaned["SUPABASE_SERVICE_ROLE_KEY"] = ""
    return cleaned


# Required env vars for the server subprocess (strict config).
_SERVER_ENV_DEFAULTS: dict[str, str] = {
    "OPENAI_API_KEY": "test-integration",
    "OPENAI_MODEL": "gpt-5.2",
    "OPENAI_TEMPERATURE": "0.0",
    "OPENAI_MAX_TOKENS": "16000",
    "OPENAI_MAX_OUTPUT_TOKENS": "900",
    "GOOGLE_API_KEY": "test-integration",
    "GOOGLE_MODEL": "gemini-2.0-flash",
    "LORA_BASE_URL": "https://fake.example.com",
    "LORA_SYSTEM_PROMPT_FILE": "config/lora_system_prompt.txt",
    "LORA_USER_PROMPT_FILE": "config/lora_user_prompt.txt",
    "LORA_STAGE1_USER_PROMPT_FILE": "config/lora_user_prompt.txt",
    "LORA_STAGE2_USER_PROMPT_FILE": "config/lora_user_prompt_OCR.txt",
    "CHATGPT_SYSTEM_PROMPT_FILE": "config/chatgpt_system_prompt_image.txt",
    "CHATGPT_USER_PROMPT_FILE": "config/chatgpt_user_prompt_image.txt",
    "CHATGPT_STAGE2_SYSTEM_PROMPT_FILE": "config/chatgpt_system_prompt_image.txt",
    "CHATGPT_STAGE2_USER_PROMPT_FILE": "config/chatgpt_user_prompt_image.txt",
    "AXEDRAS_BASE_URL": "https://instance1.acc.axedras.io",
    "AXEDRAS_KEYCLOAK_URL": "https://keycloak.acc.axedras.io",
    "AXEDRAS_REALM": "instance1",
    "AXEDRAS_USERNAME": "user",
    "AXEDRAS_PASSWORD": "pass",
    "AXEDRAS_CLIENT_ID": "axedras-api",
    "SERVER_HOST": "0.0.0.0",
    "SERVER_PORT": "8000",
    "SERVER_WORKERS": "4",
    "MAX_TEST_IMAGES": "10",
    "STRATEGY_IMAGE_WORKERS": "0",
}


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

    env = _remove_supabase_env(
        {
            **_SERVER_ENV_DEFAULTS,
            **os.environ,
            "PYTHONPATH": str(PROJECT_ROOT / "src"),
            "XSCANNER_DOTENV_OVERRIDE": "false",
        }
    )

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
        env=env,
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
def server_with_mock_error():
    """Start a server instance that forces mock errors.

    We use a separate server instance so only tests that need mock errors
    opt into the behavior.
    """

    # Get a free port
    sock = socket.socket()
    sock.bind(("", 0))
    port = sock.getsockname()[1]
    sock.close()

    server_url = f"http://127.0.0.1:{port}"

    env = _remove_supabase_env(
        {
            **_SERVER_ENV_DEFAULTS,
            **os.environ,
            "PYTHONPATH": str(PROJECT_ROOT / "src"),
            "XSCANNER_DOTENV_OVERRIDE": "false",
            "XSCANNER_MOCK_FORCE_ERROR": "true",
        }
    )

    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "xscanner.server.server:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--log-level",
            "warning",
        ],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for server to start
    for _ in range(20):
        try:
            response = httpx.get(f"{server_url}/health", timeout=1.0)
            if response.status_code == 200:
                break
        except (httpx.ConnectError, httpx.TimeoutException, httpx.ReadTimeout):
            time.sleep(0.5)
    else:
        process.kill()
        raise RuntimeError(f"Server failed to start on port {port}")

    yield server_url

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
        """Test extraction endpoint with mock mode enabled (local=LoRA)."""
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
        # Strategy should be LoRA-related for local
        assert "lora" in data["strategy_used"].lower()
        assert "(mock)" in data["strategy_used"]
        assert "structured_data" in data
        assert "request_id" in data

    def test_extract_with_forced_mock_error(self, server_with_mock_error, test_image_bytes):
        """Mock error forcing should produce a deterministic error response."""
        image_b64 = base64.b64encode(test_image_bytes).decode("utf-8")

        response = httpx.post(
            f"{server_with_mock_error}/extract",
            json={
                "image_base64": image_b64,
                "strategy": "local",
                "use_mock": True,
            },
            timeout=10.0,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data.get("error")
        assert data.get("request_id")

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

    def test_extract_upload_mock_selects_response_by_filename(self, server, test_image_bytes):
        """Mock-mode upload should select the mock entry matching the uploaded filename."""

        mockdata_path = PROJECT_ROOT / "src" / "xscanner" / "mockdata" / "extraction_responses.json"
        extraction_data = json.loads(mockdata_path.read_text())

        selected_filename = None
        expected_structured_data = None

        # Pick any entry that has a non-error LoRA result so the response is deterministic.
        for entry in extraction_data:
            for strategy_name, result in entry.get("results", {}).items():
                if (
                    "LoRA" in strategy_name
                    and not result.get("error")
                    and result.get("structured_data")
                ):
                    selected_filename = entry.get("image")
                    expected_structured_data = result.get("structured_data")
                    break
            if selected_filename:
                break

        assert selected_filename, "No suitable LoRA mock entry found in extraction_responses.json"
        assert expected_structured_data is not None

        response = httpx.post(
            f"{server}/extract/upload",
            files={"file": (selected_filename, test_image_bytes, "image/jpeg")},
            data={
                "strategy": "local",
                "use_mock": "true",
            },
            timeout=5.0,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "lora" in data["strategy_used"].lower()
        assert "(mock)" in data["strategy_used"]
        assert data["structured_data"] == expected_structured_data

    def test_extract_upload_mock_matches_ground_truth_for_known_fixture(
        self, server, test_image_bytes
    ):
        """Mock-mode local upload should be consistent with filename ground truth.

        This picks a fixture entry whose LoRA mock structured_data validates against
        ground truth parsed from the filename.
        """

        mockdata_path = PROJECT_ROOT / "src" / "xscanner" / "mockdata" / "extraction_responses.json"
        extraction_data = json.loads(mockdata_path.read_text())

        selected_filename = None
        expected_ground_truth = None

        for entry in extraction_data:
            filename = str(entry.get("image") or "").strip()
            if not filename:
                continue

            try:
                ground_truth = parse_filename_ground_truth(Path(filename))
            except Exception:
                continue

            if not ground_truth:
                continue

            for strategy_name, result in entry.get("results", {}).items():
                if "LoRA" not in strategy_name:
                    continue
                if result.get("error"):
                    continue
                structured = result.get("structured_data") or {}
                if not isinstance(structured, dict) or not structured:
                    continue

                _, errors = validate_extraction(structured, ground_truth)
                if not errors:
                    selected_filename = filename
                    expected_ground_truth = ground_truth
                    break

            if selected_filename:
                break

        assert selected_filename, "No LoRA mock entry found that matches filename ground truth"
        assert expected_ground_truth is not None

        response = httpx.post(
            f"{server}/extract/upload",
            files={"file": (selected_filename, test_image_bytes, "image/jpeg")},
            data={
                "strategy": "local",
                "use_mock": "true",
            },
            timeout=5.0,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "lora" in data["strategy_used"].lower()
        assert "(mock)" in data["strategy_used"]

        _, errors = validate_extraction(data["structured_data"], expected_ground_truth)
        assert errors == [], f"Expected no validation errors, got: {errors}"

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
        assert "lora" in data["strategy_used"].lower()
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
        assert "lora" in data["strategy_used"].lower(), (
            f"Expected local strategy, got: {data['strategy_used']}"
        )

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
        """Test that strategy='local' uses LoRA strategy."""
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
        assert "lora" in data["strategy_used"].lower(), (
            f"Expected local strategy, got: {data['strategy_used']}"
        )

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
        assert "lora" in data["strategy_used"].lower()
