"""AI integration layer (provider-agnostic core + domain runners).

This package provides a stable boundary around external AI/model providers
(e.g. OpenAI) so domain code can focus on prompts, schemas and mapping.
"""

from .factory.ai_factory import AiFactory

__all__ = ["AiFactory"]
