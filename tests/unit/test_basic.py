"""Test placeholder for xScanner."""


def test_placeholder():
    """Placeholder test - replace with actual tests."""
    # Simple import check to verify package structure
    import xscanner

    assert xscanner is not None


def test_config_loading():
    """Test configuration module loads without error."""
    from xscanner.server.config import AppConfig

    # Test default config creation
    config = AppConfig()
    assert config.server.port == 8000
    assert config.openai.model == "gpt-4o-mini"


def test_extraction_strategy_enum():
    """Test extraction strategy enum values."""
    from xscanner.server.extraction import ExtractionStrategy

    assert ExtractionStrategy.LOCAL.value == "local"
    assert ExtractionStrategy.CLOUD.value == "cloud"
