"""Image and strategy discovery utilities for CLI tools."""

import os
import sys
from pathlib import Path

# Add src to path for imports (repo uses src/ layout)
SRC_DIR = Path(__file__).resolve().parents[2] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from xscanner.strategy.base import ExtractionStrategy  # noqa: E402
from xscanner.strategy.chatgpt_vision_strategy import ChatGPTVisionStrategy  # noqa: E402
from xscanner.strategy.gemini_flash_strategy import GeminiFlashStrategy  # noqa: E402

# Optional local / hybrid strategies
try:  # noqa: E402
    from xscanner.strategy.lora_finetuned_strategy import LoRAFinetunedStrategy
    from xscanner.strategy.minicpm_v_strategy import MiniCPMVStrategy
    from xscanner.strategy.qwen3_vision_strategy import Qwen3VisionStrategy
except Exception:  # pragma: no cover
    LoRAFinetunedStrategy = None
    MiniCPMVStrategy = None
    Qwen3VisionStrategy = None

try:  # noqa: E402
    from xscanner.strategy.hybrid import (
        MiniCPMQwenHybridV2,
        MiniCPMQwenHybridV3,
        QwenMiniCPMHybridV2,
        QwenMiniCPMHybridV3,
    )
except Exception:  # pragma: no cover
    MiniCPMQwenHybridV2 = None
    MiniCPMQwenHybridV3 = None
    QwenMiniCPMHybridV2 = None
    QwenMiniCPMHybridV3 = None

try:  # noqa: E402
    from xscanner.strategy.paddle_ollama_hybrid_strategy import PaddleLlamaHybridStrategy
except Exception:  # pragma: no cover
    PaddleLlamaHybridStrategy = None

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


def get_available_strategies() -> dict[str, type[ExtractionStrategy]]:
    """Get map of strategy names to classes."""
    strategies: dict[str, type[ExtractionStrategy]] = {}

    if os.environ.get("OPENAI_API_KEY"):
        strategies["chatgpt"] = ChatGPTVisionStrategy

    if os.environ.get("GOOGLE_API_KEY"):
        strategies["gemini"] = GeminiFlashStrategy

    if Qwen3VisionStrategy and Qwen3VisionStrategy.is_available():
        strategies["qwen3"] = Qwen3VisionStrategy

    if MiniCPMVStrategy and MiniCPMVStrategy.is_available():
        strategies["minicpm"] = MiniCPMVStrategy

    if LoRAFinetunedStrategy and LoRAFinetunedStrategy.is_available():
        strategies["lora"] = LoRAFinetunedStrategy

    if QwenMiniCPMHybridV2 and QwenMiniCPMHybridV2.is_available():
        strategies["hybrid-v2-qwen-first"] = QwenMiniCPMHybridV2
    if MiniCPMQwenHybridV2 and MiniCPMQwenHybridV2.is_available():
        strategies["hybrid-v2-minicpm-first"] = MiniCPMQwenHybridV2
    if QwenMiniCPMHybridV3 and QwenMiniCPMHybridV3.is_available():
        strategies["hybrid-v3-qwen-first"] = QwenMiniCPMHybridV3
    if MiniCPMQwenHybridV3 and MiniCPMQwenHybridV3.is_available():
        strategies["hybrid-v3-minicpm-first"] = MiniCPMQwenHybridV3

    # Legacy hybrid (optional)
    if PaddleLlamaHybridStrategy and PaddleLlamaHybridStrategy.is_available():
        strategies["hybrid"] = PaddleLlamaHybridStrategy

    return strategies


def create_strategy(strategy_name: str) -> ExtractionStrategy:
    """Create strategy instance by name."""
    strategies = get_available_strategies()

    if strategy_name not in strategies:
        raise ValueError(f"Strategy '{strategy_name}' not available")

    strategy_class = strategies[strategy_name]

    if strategy_name == "chatgpt":
        return ChatGPTVisionStrategy()
    elif strategy_name == "gemini":
        return GeminiFlashStrategy()
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
    """List available extraction strategies with configuration status."""
    strategies = get_available_strategies()

    if not strategies:
        print("❌ No strategies available. Check your API keys in .env.local")
        return

    print(f"\n🤖 Available Strategies ({len(strategies)}):\n")
    for name in strategies:
        print(f"  - {name}")

    print("\n💡 Configuration:")
    print(
        f"  OpenAI API Key: {'✅ Configured' if os.environ.get('OPENAI_API_KEY') else '❌ Missing'}"
    )
    print(
        f"  Google API Key: {'✅ Configured' if os.environ.get('GOOGLE_API_KEY') else '❌ Missing'}"
    )
