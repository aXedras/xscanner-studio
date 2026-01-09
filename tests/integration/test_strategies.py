"""Integration tests for extraction strategies.

These tests may require API keys and/or locally running services.
They are intentionally marked as integration tests.
"""

import pytest

from tools.cli.comparator import StrategyComparator
from xscanner.server.config import get_config
from xscanner.strategy.chatgpt_vision_strategy import ChatGPTVisionStrategy
from xscanner.strategy.gemini_flash_strategy import GeminiFlashStrategy

from .test_helpers import collect_image_paths

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def config():
    return get_config()


@pytest.fixture(scope="module")
def test_images():
    images = collect_image_paths()
    if not images:
        pytest.skip("No test images found")
    return images[:3]


@pytest.fixture(scope="module")
def chatgpt_strategy(config):
    if not config.openai.api_key:
        pytest.skip("OPENAI_API_KEY not configured")
    return ChatGPTVisionStrategy(
        api_key=config.openai.api_key,
        model=config.openai.model,
        temperature=config.openai.temperature,
        max_output_tokens=config.openai.max_output_tokens,
    )


@pytest.fixture(scope="module")
def gemini_strategy(config):
    if not config.google.api_key:
        pytest.skip("GOOGLE_API_KEY not configured")
    return GeminiFlashStrategy(api_key=config.google.api_key)


def test_chatgpt_extract(chatgpt_strategy, test_images):
    for image_path in test_images:
        result = chatgpt_strategy.extract(image_path)
        assert result is not None
        assert result.processing_time > 0
        assert result.strategy_name.startswith("ChatGPT Vision")


def test_gemini_extract(gemini_strategy, test_images):
    for image_path in test_images:
        result = gemini_strategy.extract(image_path)
        assert result is not None
        assert result.processing_time > 0
        assert result.strategy_name.startswith("Gemini")


def test_strategy_comparison(config, test_images):
    strategies = []

    if config.openai.api_key:
        strategies.append(
            ChatGPTVisionStrategy(
                api_key=config.openai.api_key,
                model=config.openai.model,
            )
        )

    if config.google.api_key:
        strategies.append(GeminiFlashStrategy(api_key=config.google.api_key))

    if not strategies:
        pytest.skip("No API keys configured for comparison test")

    comparator = StrategyComparator(strategies=strategies, max_workers=1)
    results = comparator.test_image(test_images[0])
    assert len(results) == len(strategies)
    for _strategy_name, result in results.items():
        assert result is not None
        assert result.processing_time > 0
