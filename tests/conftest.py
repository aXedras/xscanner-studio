"""Pytest configuration and shared fixtures for xScanner tests."""

from collections.abc import Generator
from pathlib import Path

import pytest

from xscanner.server.config import AppConfig, GoogleConfig, OpenAIConfig, ServerConfig


@pytest.fixture
def sample_config() -> AppConfig:
    """Provide test configuration with mock values."""
    return AppConfig(
        openai=OpenAIConfig(
            api_key="test_openai_key",
            model="gpt-5.2",
            temperature=0.0,
            max_tokens=16000,
            max_output_tokens=16000,
        ),
        google=GoogleConfig(
            api_key="test_google_key",
            model="gemini-2.0-flash-exp",
        ),
        server=ServerConfig(
            host="localhost",
            port=8000,
            reload=False,
        ),
    )


@pytest.fixture
def test_image_path(tmp_path: Path) -> Path:
    """Create a temporary test image file."""
    image_path = tmp_path / "test_image.jpg"
    # Create a minimal valid JPEG file (1x1 pixel)
    jpeg_data = bytes.fromhex(
        "ffd8ffe000104a46494600010101004800480000"
        "ffdb004300080606070605080707070909080a0c"
        "140d0c0b0b0c1912130f141d1a1f1e1d1a1c1c20"
        "2428342c202430241c1c2c402c303433342f3033"
        "30ffdb0043010909090c0b0c180d0d1832211c21"
        "32323232323232323232323232323232323232323232"
        "32323232323232323232323232323232323232323232"
        "323232ffc00011080001000103012200021101031101"
        "ffc4001500010100000000000000000000000000000000"
        "ffc40014100100000000000000000000000000000000"
        "ffc40014010100000000000000000000000000000000"
        "ffc40014110100000000000000000000000000000000"
        "ffda000c03010002110311003f00bf800ffd9"
    )
    image_path.write_bytes(jpeg_data)
    return image_path


@pytest.fixture
def temp_test_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    test_dir = tmp_path / "xscanner_test"
    test_dir.mkdir()
    yield test_dir
    # Cleanup happens automatically with tmp_path


# Pytest markers
def pytest_configure(config):
    """Register custom pytest markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test (requires external dependencies)"
    )
    config.addinivalue_line("markers", "slow: mark test as slow (takes >1s to run)")
    config.addinivalue_line("markers", "requires_api_key: mark test as requiring API credentials")
