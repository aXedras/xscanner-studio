"""Integration tests for extraction strategy interfaces.

These tests validate the strategy contracts and implementations
without making real network/API calls (external dependencies are mocked).
"""

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from xscanner.strategy.base import ExtractionResult, ExtractionStrategy
from xscanner.strategy.chatgpt_vision_strategy import ChatGPTVisionStrategy
from xscanner.strategy.gemini_flash_strategy import GeminiFlashStrategy
from xscanner.strategy.lora_finetuned_strategy import LoRAFinetunedStrategy

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
    def strategy(self, monkeypatch):
        """Create strategy with mock env vars."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("OPENAI_MODEL", "gpt-5.2")
        monkeypatch.setenv("OPENAI_TEMPERATURE", "0.0")
        monkeypatch.setenv("OPENAI_MAX_OUTPUT_TOKENS", "900")
        monkeypatch.setenv("OPENAI_API_URL", "https://api.openai.com/v1/responses")
        monkeypatch.setenv("CHATGPT_SYSTEM_PROMPT_FILE", "config/chatgpt_system_prompt_image.txt")
        monkeypatch.setenv("CHATGPT_USER_PROMPT_FILE", "config/chatgpt_user_prompt_image.txt")
        return ChatGPTVisionStrategy()

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
        """Strategy initializes with correct configuration from env vars."""
        assert strategy.name.startswith("ChatGPT Vision")
        # Values come from fixture's monkeypatch.setenv
        assert strategy.model == "gpt-5.2"
        assert strategy.temperature == 0.0

    @patch("requests.Session.post")
    def test_extract_returns_result(self, mock_post, strategy, mock_image_path):
        # Mock Responses API format with output_text shortcut
        mock_data = {
            "category": "bar",
            "metal": "Gold",
            "weight": 1000,
            "weight_unit": "g",
            "fineness": 999.9,
            "serial_number": "AR95742",
            "serial_number_visibility": "clearly_visible",
            "producer": "Valcambi",
            "visible_damage": False,
        }
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_response.text = json.dumps({"output_text": json.dumps(mock_data)})
        mock_response.json.return_value = {
            "output_text": json.dumps(mock_data),
        }
        mock_post.return_value = mock_response

        result = strategy.extract(mock_image_path)

        assert isinstance(result, ExtractionResult)
        assert result.strategy_name.startswith("ChatGPT Vision")
        assert result.processing_time >= 0
        assert isinstance(result.structured_data, dict)
        assert result.error is None
        # Verify data from mock (new snake_case field names)
        assert result.structured_data.get("metal") == "Gold"
        assert result.structured_data.get("producer") == "Valcambi"
        assert result.structured_data.get("serial_number") == "AR95742"

    def test_extract_handles_invalid_path(self, strategy):
        """Extract raises FileNotFoundError for non-existent file."""
        invalid_path = Path("/nonexistent/image.jpg")

        with pytest.raises(FileNotFoundError):
            strategy.extract(invalid_path)


class TestGeminiFlashStrategy:
    """Test Gemini Flash strategy without real API calls."""

    @pytest.fixture
    def strategy(self, monkeypatch):
        """Create strategy with mock API key and env vars."""
        monkeypatch.setenv("CHATGPT_SYSTEM_PROMPT_FILE", "config/chatgpt_system_prompt_image.txt")
        monkeypatch.setenv("CHATGPT_USER_PROMPT_FILE", "config/chatgpt_user_prompt_image.txt")
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


class TestLoRAFinetunedStrategy:
    """Test LoRA fine-tuned strategy without real network calls."""

    @pytest.fixture
    def strategy(self, monkeypatch):
        """Create strategy with mock configuration."""
        monkeypatch.setenv("LORA_SYSTEM_PROMPT_FILE", "config/lora_system_prompt.txt")
        monkeypatch.setenv("LORA_USER_PROMPT_FILE", "config/lora_user_prompt.txt")
        # LoRA strategy validates base URL at init; mock that in tests.
        with patch("requests.get") as mock_get:
            mock_get.return_value = Mock(status_code=200)
            return LoRAFinetunedStrategy(base_url="http://lora.test", timeout=5)

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
        assert strategy.name.startswith("LoRA")

    @patch("requests.post")
    def test_extract_returns_result(self, mock_post, strategy, mock_image_path):
        """Extract method returns ExtractionResult with realistic mocked response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "data": {
                "metal": "AU",
                "weight": 1000,
                "weight_unit": "g",
                "fineness": 0.9999,
                "serial_number": "AR95742",
                "producer": "Valcambi",
            },
            "raw_output": "{...}",
        }
        mock_post.return_value = mock_response

        result = strategy.extract(mock_image_path)

        # Verify structure
        assert isinstance(result, ExtractionResult)
        assert result.processing_time >= 0
        assert isinstance(result.structured_data, dict)

        assert result.structured_data.get("Metal") == "Gold"
        assert result.structured_data.get("Producer") == "Valcambi"
        assert result.structured_data.get("SerialNumber") == "AR95742"

    def test_extract_handles_invalid_path(self, strategy):
        """Extract handles non-existent file path gracefully."""
        invalid_path = Path("/nonexistent/image.jpg")

        # Strategy wraps errors in ExtractionResult.error, doesn't raise
        result = strategy.extract(invalid_path)
        assert result.error is not None or result.structured_data == {}
