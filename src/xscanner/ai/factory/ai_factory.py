from __future__ import annotations

from dataclasses import dataclass

from xscanner.ai.infrastructure.openai_client import (
    OpenAIChatCompletionsClient,
    OpenAIClientConfig,
)
from xscanner.lib.logging import get_logger
from xscanner.server.config import get_config


@dataclass(frozen=True)
class AiFactory:
    """Factory for AI clients and domain runners.

    Mirrors the Studio ServiceFactory pattern: one place to wire dependencies.
    """

    openai: OpenAIChatCompletionsClient

    @staticmethod
    def build() -> AiFactory:
        logger = get_logger("AiFactory")
        cfg = get_config()

        openai_cfg = OpenAIClientConfig(
            api_key=cfg.openai.api_key,
            model=cfg.openai.model,
            temperature=cfg.openai.temperature,
            max_output_tokens=cfg.openai.max_output_tokens,
        )

        logger.debug(
            "AI factory configured (provider=openai, model=%s, api_key_set=%s)",
            openai_cfg.model,
            bool(openai_cfg.api_key),
        )

        return AiFactory(openai=OpenAIChatCompletionsClient(openai_cfg))
