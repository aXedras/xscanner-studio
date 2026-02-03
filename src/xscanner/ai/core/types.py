from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


class AiError(RuntimeError):
    """Base error for AI integration failures."""


class AiConfigurationError(AiError):
    """Raised when required configuration (e.g. API key) is missing."""


class AiProviderError(AiError):
    """Raised when a provider API call fails."""


class AiResponseFormatError(AiError):
    """Raised when a provider response cannot be parsed as expected."""


AiRole = Literal["system", "user", "assistant"]


@dataclass(frozen=True)
class AiMessage:
    role: AiRole
    content: str


@dataclass(frozen=True)
class AiRequest:
    model: str
    messages: list[AiMessage]
    temperature: float = 0.2
    max_output_tokens: int = 900
    force_json: bool = True


@dataclass(frozen=True)
class AiUsage:
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None


@dataclass(frozen=True)
class AiResponse:
    text: str
    provider: str
    model: str
    usage: AiUsage
    raw: dict[str, Any]
