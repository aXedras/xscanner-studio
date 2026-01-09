"""Integration tests for extraction strategy service interfaces.

These tests validate the strategy interfaces and implementations
without making real API calls (mocked external dependencies).
"""

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from xscanner.strategy.base import ExtractionResult, ExtractionStrategy
from xscanner.strategy.chatgpt_vision_strategy import ChatGPTVisionStrategy
from xscanner.strategy.gemini_flash_strategy import GeminiFlashStrategy

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def chatgpt_fixture():
    """Load realistic ChatGPT response from fixture."""
    fixture_path = Path(__file__).parent.parent / "fixtures" / "chatgpt_response.json"
    return json.loads(fixture_path.read_text())


@pytest.fixture(scope="module")
def gemini_fixture():
    """Load realistic Gemini response from fixture."""
    fixture_path = Path(__file__).parent.parent / "fixtures" / "gemini_response.json"
    return json.loads(fixture_path.read_text())


class TestExtractionStrategyInterface:
    """Test base strategy interface contract."""

    def test_strategy_has_required_methods(self):
        """All strategies must implement extract() method."""
        # Verify interface exists
        assert hasattr(ExtractionStrategy, "extract")
        assert hasattr(ExtractionStrategy, "name")

    def test_extraction_result_structure(self):
        """ExtractionResult must have required attributes."""
        result = ExtractionResult(
            strategy_name="Test Strategy",
            processing_time=0.5,
            raw_text="test raw text",
            structured_data={"metal": "gold"},
            confidence=0.95,
        )

        assert result.strategy_name == "Test Strategy"
        assert result.processing_time == 0.5
        assert result.raw_text == "test raw text"
        assert result.structured_data == {"metal": "gold"}
        assert result.confidence == 0.95


class TestChatGPTVisionStrategy:
    """Test ChatGPT Vision strategy without real API calls."""

    @pytest.fixture
    def strategy(self):
        """Create strategy with mock API key."""
        return ChatGPTVisionStrategy(
            api_key="test-key",
            model="gpt-4o-mini",
        )

    @pytest.fixture
    def mock_image_path(self, tmp_path):
        """Create a temporary test image."""
        image_path = tmp_path / "test.jpg"
        # Create minimal valid JPEG
        image_path.write_bytes(
            b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xd9"
        )
        return image_path

    def test_strategy_initialization(self, strategy):
        """Strategy initializes with correct configuration."""
        assert strategy.name.startswith("ChatGPT Vision")
        assert "gpt-4o-mini" in strategy.name

    @patch("requests.Session.request")
    def test_extract_returns_result(self, mock_request, strategy, mock_image_path, chatgpt_fixture):
        """Extract method returns ExtractionResult with realistic mocked API response."""
        # Mock HTTP API response with realistic data from fixture
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": chatgpt_fixture["raw_text"]}}]
        }
        mock_request.return_value = mock_response

        # Execute
        result = strategy.extract(mock_image_path)

        # Verify structure
        assert isinstance(result, ExtractionResult)
        assert result.strategy_name.startswith("ChatGPT Vision")
        assert result.processing_time >= 0
        assert isinstance(result.structured_data, dict)

        # Verify realistic data from fixture
        expected = chatgpt_fixture["structured_data"]
        assert result.structured_data.get("Metal") == expected.get("Metal")
        assert result.structured_data.get("Producer") == expected.get("Producer")

    def test_extract_handles_invalid_path(self, strategy):
        """Extract handles non-existent file path gracefully."""
        invalid_path = Path("/nonexistent/image.jpg")

        # Strategy wraps errors in ExtractionResult.error, doesn't raise
        result = strategy.extract(invalid_path)
        assert result.error is not None or result.structured_data == {}


class TestGeminiFlashStrategy:
    """Test Gemini Flash strategy without real API calls."""

    @pytest.fixture
    def strategy(self):
        """Create strategy with mock API key."""
        return GeminiFlashStrategy(api_key="test-key")

    @pytest.fixture
    def mock_image_path(self, tmp_path):
        """Create a temporary test image."""
        image_path = tmp_path / "test.jpg"
        # Create minimal valid JPEG
        image_path.write_bytes(
            b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xd9"
        )
        return image_path

    def test_strategy_initialization(self, strategy):
        """Strategy initializes with correct configuration."""
        assert strategy.name.startswith("Gemini")

    @patch("requests.Session.post")
    def test_extract_returns_result(self, mock_post, strategy, mock_image_path, gemini_fixture):
        """Extract method returns ExtractionResult with realistic mocked API response."""
        # Mock HTTP response from Gemini REST API with realistic data from fixture
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "candidates": [{"content": {"parts": [{"text": gemini_fixture["raw_text"]}]}}]
        }
        mock_post.return_value = mock_response

        # Execute
        result = strategy.extract(mock_image_path)

        # Verify structure
        assert isinstance(result, ExtractionResult)
        assert result.strategy_name.startswith("Gemini")
        assert result.processing_time >= 0
        assert isinstance(result.structured_data, dict)

        # Verify realistic data from fixture
        expected = gemini_fixture["structured_data"]
        assert result.structured_data.get("Metal") == expected.get("Metal")
        assert result.structured_data.get("Producer") == expected.get("Producer")

    def test_extract_handles_invalid_path(self, strategy):
        """Extract handles non-existent file path gracefully."""
        invalid_path = Path("/nonexistent/image.jpg")

        # Strategy wraps errors in ExtractionResult.error, doesn't raise
        result = strategy.extract(invalid_path)
        assert result.error is not None or result.structured_data == {}
