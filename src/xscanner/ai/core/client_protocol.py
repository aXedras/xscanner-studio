from __future__ import annotations

from typing import Protocol

from xscanner.ai.core.types import AiRequest, AiResponse


class AiClient(Protocol):
    def complete(self, request: AiRequest) -> AiResponse:
        raise NotImplementedError
