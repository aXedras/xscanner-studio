"""Pytest configuration for e2e tests."""

import sys
from pathlib import Path

import pytest

# Add integration test helpers to path
sys.path.insert(0, str(Path(__file__).parent.parent / "integration"))


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--quality-check",
        action="store_true",
        default=False,
        help="Run in quality check mode: report all errors but don't fail tests",
    )


@pytest.fixture
def quality_check_mode(request):
    """Return True if running in quality check mode."""
    return request.config.getoption("--quality-check")
