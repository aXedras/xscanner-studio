"""Image and strategy discovery utilities for CLI tools."""

from pathlib import Path

from xscanner.server.config import get_config
from xscanner.strategy.base import OCRStrategy
from xscanner.strategy.chatgpt_vision_strategy import ChatGPTVisionStrategy
from xscanner.strategy.gemini_flash_strategy import GeminiFlashStrategy
from xscanner.strategy.paddle_llama_hybrid_strategy import PaddleLlamaHybridStrategy

IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png")
SEARCH_PATHS = [
    Path("barPictures") / "Renamed-and-Sorted Au, Ag, Pt",
    Path("barPictures") / "difficult",
    Path("barPictures"),
    Path("invoices"),
]


def find_all_images() -> list[Path]:
    """Find all image files in standard locations."""
    images = []
    seen = set()

    for search_path in SEARCH_PATHS:
        if not search_path.exists():
            continue
        for img_path in search_path.rglob("*"):
            if img_path.suffix.lower() in IMAGE_EXTENSIONS:
                key = str(img_path.resolve())
                if key not in seen:
                    seen.add(key)
                    images.append(img_path)

    return sorted(images)


def get_available_strategies() -> dict[str, type[OCRStrategy]]:
    """Get map of strategy names to classes."""
    config = get_config()

    strategies: dict[str, type[OCRStrategy]] = {}

    if config.openai.api_key:
        strategies["chatgpt"] = ChatGPTVisionStrategy

    if config.google.api_key:
        strategies["gemini"] = GeminiFlashStrategy

    strategies["hybrid"] = PaddleLlamaHybridStrategy

    return strategies


def create_strategy(strategy_name: str) -> OCRStrategy:
    """Create strategy instance by name."""
    config = get_config()
    strategies = get_available_strategies()

    if strategy_name not in strategies:
        raise ValueError(f"Strategy '{strategy_name}' not available")

    strategy_class = strategies[strategy_name]

    if strategy_name == "chatgpt":
        return ChatGPTVisionStrategy(
            api_key=config.openai.api_key,
            model=config.openai.model,
        )
    elif strategy_name == "gemini":
        return GeminiFlashStrategy(api_key=config.google.api_key)
    elif strategy_name == "hybrid":
        return PaddleLlamaHybridStrategy(base_url=config.ollama.base_url)
    else:
        return strategy_class()


def list_images_info():
    """List all available test images with details."""
    images = find_all_images()

    if not images:
        print("❌ No images found in standard locations")
        return

    print(f"\n📸 Found {len(images)} images:\n")
    for idx, img in enumerate(images, 1):
        size_kb = img.stat().st_size / 1024
        try:
            display_path = img.relative_to(Path.cwd())
        except ValueError:
            display_path = img
        print(f"  {idx:3d}. {display_path} ({size_kb:.1f} KB)")


def list_strategies_info():
    """List available OCR strategies with configuration status."""
    strategies = get_available_strategies()

    if not strategies:
        print("❌ No strategies available. Check your API keys in .env.local")
        return

    config = get_config()

    print(f"\n🤖 Available OCR Strategies ({len(strategies)}):\n")
    for name in strategies:
        print(f"  - {name}")

    print("\n💡 Configuration:")
    print(f"  OpenAI API Key: {'✅ Configured' if config.openai.api_key else '❌ Missing'}")
    print(f"  Google API Key: {'✅ Configured' if config.google.api_key else '❌ Missing'}")
    print(f"  Ollama URL: {config.ollama.base_url}")
