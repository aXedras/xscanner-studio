"""End-to-end tests for server persistence behavior.

These tests verify Supabase persistence (DB + Storage) and error semantics.
They are intentionally marked as e2e because they require local Supabase.
"""

import base64
import io
import json
import os
import re
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest
from PIL import Image

from tests.integration.test_helpers import get_random_test_image

pytestmark = pytest.mark.e2e


def _redact_secrets(text: str) -> str:
    # Best-effort redaction to avoid leaking secrets in CI logs.
    text = re.sub(r"sb_secret_[A-Za-z0-9_-]+", "sb_secret_<redacted>", text)
    text = re.sub(r"sk-(?:proj-)?[A-Za-z0-9_-]+", "sk-<redacted>", text)
    return text


def _drain_process_output(process: subprocess.Popen) -> tuple[str, str]:
    try:
        stdout_bytes, stderr_bytes = process.communicate(timeout=1)
    except subprocess.TimeoutExpired:
        stdout_bytes = b""
        stderr_bytes = b""
    stdout = _redact_secrets((stdout_bytes or b"").decode("utf-8", errors="replace"))
    stderr = _redact_secrets((stderr_bytes or b"").decode("utf-8", errors="replace"))
    return stdout, stderr


def _wait_for_server_or_raise(*, process: subprocess.Popen, server_url: str, port: int) -> None:
    for _ in range(60):
        if process.poll() is not None:
            stdout, stderr = _drain_process_output(process)
            raise RuntimeError(
                "Server process exited before becoming healthy. "
                f"port={port} returncode={process.returncode}\n"
                f"STDOUT:\n{stdout}\nSTDERR:\n{stderr}"
            )

        try:
            response = httpx.get(f"{server_url}/health", timeout=1.0)
            if response.status_code == 200:
                return
        except (httpx.ConnectError, httpx.TimeoutException, httpx.ReadTimeout):
            time.sleep(0.5)

    # Timed out: capture whatever we can and fail loudly.
    process.kill()
    stdout, stderr = _drain_process_output(process)
    raise RuntimeError(
        f"Server failed to start on port {port}\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}"
    )


def _get_local_supabase_credentials() -> tuple[str, str]:
    """Read local Supabase URL + key from `supabase status`.

    We prefer machine-readable output because the pretty output format may
    change between Supabase CLI versions.

    These tests should fail loudly when Supabase isn't running.
    """

    try:
        output = subprocess.check_output(["supabase", "status", "-o", "json"], text=True)
    except Exception as e:
        raise RuntimeError(
            "Failed to run `supabase status`. Is the Supabase CLI installed and are you in the repo root?"
        ) from e

    try:
        data = json.loads(output)
    except Exception as e:
        raise RuntimeError(
            "Failed to parse `supabase status -o json` output. "
            "Local Supabase may not be running or the CLI output changed. "
            "Run `supabase start` and retry."
        ) from e

    # Supabase CLI provides both newer publishable/secret keys and legacy anon/service_role keys.
    # For server-side tests we prefer the secret key when available.
    supabase_url = (data.get("API_URL") or "").strip()
    supabase_key = (
        (data.get("SECRET_KEY") or "")
        or (data.get("SERVICE_ROLE_KEY") or "")
        or (data.get("ANON_KEY") or "")
    ).strip()

    if not supabase_url or not supabase_key:
        raise RuntimeError(
            "Local Supabase is not running or required keys are missing. "
            "Run `supabase start` and retry. "
            f"available_keys={sorted([k for k, v in data.items() if v])}"
        )

    return supabase_url, supabase_key


def _base_env_without_supabase() -> dict[str, str]:
    """Return a base env dict without inherited SUPABASE_* vars.

    We then set explicit Supabase vars per test to keep behavior deterministic.
    """

    base = dict(os.environ)
    for key in list(base.keys()):
        if key.startswith("SUPABASE_"):
            base.pop(key, None)
    return base


def _supabase_headers(service_role_key: str) -> dict[str, str]:
    return {
        "apikey": service_role_key,
        "Authorization": f"Bearer {service_role_key}",
    }


def _fetch_extraction_rows(
    *, supabase_url: str, service_role_key: str, image_filename: str
) -> list[dict]:
    url = (
        f"{supabase_url.rstrip('/')}/rest/v1/extraction"
        f"?select=id,image_filename,status,error,created_at"
        f"&image_filename=eq.{image_filename}"
        f"&order=created_at.desc"
    )
    response = httpx.get(url, headers=_supabase_headers(service_role_key), timeout=5.0)
    response.raise_for_status()
    data = response.json()
    assert isinstance(data, list)
    return data


@pytest.fixture(scope="module")
def supabase_creds():
    return _get_local_supabase_credentials()


@pytest.fixture(scope="module")
def free_port():
    sock = socket.socket()
    sock.bind(("", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


@pytest.fixture(scope="module")
def server(free_port, supabase_creds):
    server_url = f"http://127.0.0.1:{free_port}"
    supabase_url, supabase_service_role_key = supabase_creds

    env = {
        **_base_env_without_supabase(),
        "XSCANNER_DOTENV": "false",
        "SUPABASE_URL": supabase_url,
        "SUPABASE_SERVICE_ROLE_KEY": supabase_service_role_key,
    }

    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "--app-dir",
            "src",
            "xscanner.server.server:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(free_port),
            "--log-level",
            "warning",
        ],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    _wait_for_server_or_raise(process=process, server_url=server_url, port=free_port)

    yield server_url

    process.terminate()
    try:
        process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        process.kill()


@pytest.fixture
def server_with_mock_error(supabase_creds):
    sock = socket.socket()
    sock.bind(("", 0))
    port = sock.getsockname()[1]
    sock.close()

    supabase_url, supabase_service_role_key = supabase_creds
    server_url = f"http://127.0.0.1:{port}"

    env = {
        **_base_env_without_supabase(),
        "XSCANNER_DOTENV": "false",
        "SUPABASE_URL": supabase_url,
        "SUPABASE_SERVICE_ROLE_KEY": supabase_service_role_key,
        "XSCANNER_MOCK_FORCE_ERROR": "true",
    }

    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "--app-dir",
            "src",
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

    _wait_for_server_or_raise(process=process, server_url=server_url, port=port)

    yield server_url

    process.terminate()
    try:
        process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        process.kill()


@pytest.fixture
def server_with_unreachable_supabase(supabase_creds):
    sock = socket.socket()
    sock.bind(("", 0))
    port = sock.getsockname()[1]
    sock.close()

    _, supabase_service_role_key = supabase_creds
    server_url = f"http://127.0.0.1:{port}"

    env = {
        **_base_env_without_supabase(),
        "XSCANNER_DOTENV": "false",
        "SUPABASE_URL": "http://127.0.0.1:1",
        "SUPABASE_SERVICE_ROLE_KEY": supabase_service_role_key,
    }

    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "--app-dir",
            "src",
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

    _wait_for_server_or_raise(process=process, server_url=server_url, port=port)

    yield server_url

    process.terminate()
    try:
        process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        process.kill()


@pytest.fixture
def test_image_bytes():
    """Return bytes for a valid JPEG image.

    Prefer a real image from the repo (barPictures), to match production-like inputs.
    Fall back to a generated JPEG when no test images are available.
    """

    image_path = get_random_test_image()
    if isinstance(image_path, Path) and image_path.exists():
        return image_path.read_bytes()

    img = Image.new("RGB", (100, 100), color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG")
    return buffer.getvalue()


def test_extract_with_mock_mode_persists_row(server, test_image_bytes, supabase_creds):
    supabase_url, supabase_service_role_key = supabase_creds
    image_b64 = base64.b64encode(test_image_bytes).decode("utf-8")

    response = httpx.post(
        f"{server}/extract",
        json={
            "image_base64": image_b64,
            "strategy": "local",
            "use_mock": True,
        },
        timeout=10.0,
    )

    assert response.status_code == 200
    data = response.json()
    assert "request_id" in data

    image_filename = f"{data['request_id']}.jpg"
    rows = _fetch_extraction_rows(
        supabase_url=supabase_url,
        service_role_key=supabase_service_role_key,
        image_filename=image_filename,
    )
    assert len(rows) >= 1
    assert rows[0].get("status") == "pending"


def test_extract_mock_error_is_persisted(server_with_mock_error, test_image_bytes, supabase_creds):
    supabase_url, supabase_service_role_key = supabase_creds
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

    image_filename = f"{data['request_id']}.jpg"
    rows = _fetch_extraction_rows(
        supabase_url=supabase_url,
        service_role_key=supabase_service_role_key,
        image_filename=image_filename,
    )
    assert len(rows) >= 1
    assert rows[0].get("error")
    assert rows[0].get("status") == "error"


def test_extract_returns_500_when_supabase_unreachable(
    server_with_unreachable_supabase, test_image_bytes
):
    image_b64 = base64.b64encode(test_image_bytes).decode("utf-8")

    response = httpx.post(
        f"{server_with_unreachable_supabase}/extract",
        json={
            "image_base64": image_b64,
            "strategy": "local",
            "use_mock": True,
        },
        timeout=10.0,
    )

    assert response.status_code == 500
    data = response.json()
    assert data["success"] is False
    assert data.get("error")
    assert data.get("request_id")
