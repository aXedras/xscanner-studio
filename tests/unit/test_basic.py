"""Test placeholder for xScanner."""


def test_placeholder():
    """Placeholder test - replace with actual tests."""
    # Simple import check to verify package structure
    import xscanner

    assert xscanner is not None


def test_config_loading(monkeypatch):
    """Test configuration module loads without error."""
    from tests.utils.env import set_required_env
    from xscanner.server.config import reload_config

    # Test config creation from env
    set_required_env(monkeypatch)
    config = reload_config()
    assert config.server.port == 8000
    assert config.openai.model == "gpt-5.2"


def test_extraction_strategy_enum():
    """Test extraction strategy enum values."""
    from xscanner.server.extraction import ExtractionStrategy

    assert ExtractionStrategy.LOCAL.value == "local"
    assert ExtractionStrategy.CLOUD.value == "cloud"
