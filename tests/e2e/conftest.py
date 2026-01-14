"""Pytest configuration for e2e tests."""

import sys
from pathlib import Path

# Add integration test helpers to path
sys.path.insert(0, str(Path(__file__).parent.parent / "integration"))
