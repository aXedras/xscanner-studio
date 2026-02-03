from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import requests

from xscanner.ai.core.types import (
    AiConfigurationError,
    AiProviderError,
    AiRequest,
    AiResponse,
    AiUsage,
)


@dataclass(frozen=True)
class OpenAIClientConfig:
    api_key: str
    model: str
    temperature: float
    max_output_tokens: int
    base_url: str = "https://api.openai.com/v1"
    timeout_seconds: float = 30.0


class OpenAIChatCompletionsClient:
    """Minimal OpenAI client using Chat Completions (KISS).

    Intentionally non-streaming and focused on JSON output.
    """

    def __init__(self, config: OpenAIClientConfig):
        if not config.api_key:
            raise AiConfigurationError("Missing OpenAI API key")

        self._config = config
        self._session = requests.Session()

    def complete(self, request: AiRequest) -> AiResponse:
        url = f"{self._config.base_url}/chat/completions"

        headers = {
            "Authorization": f"Bearer {self._config.api_key}",
            "Content-Type": "application/json",
        }

        model = request.model

        payload: dict[str, Any] = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in request.messages],
        }

        def _sanitize_payload_for_trace(payload_to_sanitize: dict[str, Any]) -> dict[str, Any]:
            """Return a JSON-serializable, secret-free snapshot of the request payload.

            Notes:
            - No headers/auth are included here.
            - Message content is truncated to keep traces reasonably sized.
            """

            max_chars = 8000
            safe: dict[str, Any] = {}
            for k, v in payload_to_sanitize.items():
                if k != "messages":
                    safe[k] = v

            messages_any = payload_to_sanitize.get("messages")
            if isinstance(messages_any, list):
                out_messages: list[dict[str, Any]] = []
                for m in messages_any:
                    if not isinstance(m, dict):
                        continue
                    role = m.get("role")
                    content = m.get("content")
                    content_str = str(content or "")
                    truncated = content_str[:max_chars]
                    out_messages.append(
                        {
                            "role": str(role or ""),
                            "content": truncated,
                            "content_len": len(content_str),
                            "content_truncated": len(content_str) > len(truncated),
                        }
                    )
                safe["messages"] = out_messages
            else:
                safe["messages"] = []

            return safe

        # Some model families (e.g. GPT-5) only support the default temperature.
        # Omit the parameter entirely for those models.
        if not model.lower().startswith("gpt-5"):
            payload["temperature"] = request.temperature

        # Some newer OpenAI model families (e.g. GPT-5) reject `max_tokens` and require
        # `max_completion_tokens` instead.
        if model.lower().startswith("gpt-5"):
            # GPT-5 counts reasoning + visible output against this budget.
            # Add a small buffer to reduce the risk of "reasoning-only" completions.
            payload["max_completion_tokens"] = int(request.max_output_tokens) + 512

            # GPT-5 may otherwise spend the entire completion budget on reasoning tokens
            # and return an empty message.content. Keep it simple and request low effort.
            payload["reasoning_effort"] = "low"
        else:
            payload["max_tokens"] = request.max_output_tokens

        # Best-effort JSON mode. If the model doesn't support it, we still parse JSON from text.
        if request.force_json:
            payload["response_format"] = {"type": "json_object"}

        def _post_and_parse(payload_to_send: dict[str, Any]) -> dict[str, Any]:
            try:
                resp = self._session.post(
                    url,
                    headers=headers,
                    data=json.dumps(payload_to_send),
                    timeout=self._config.timeout_seconds,
                )
            except requests.RequestException as exc:
                raise AiProviderError(f"OpenAI request failed: {exc}") from exc

            if resp.status_code >= 400:
                body = resp.text[:2000]
                raise AiProviderError(f"OpenAI error {resp.status_code}: {body}")

            try:
                parsed: dict[str, Any] = resp.json()
            except Exception as exc:
                raise AiProviderError(
                    f"OpenAI returned non-JSON response: {resp.text[:2000]}"
                ) from exc

            return parsed

        data = _post_and_parse(payload)

        def _extract_message_content(resp_data: dict[str, Any]) -> str:
            try:
                content = resp_data.get("choices", [{}])[0].get("message", {}).get("content", "")
            except Exception:
                content = ""
            return str(content or "")

        text = _extract_message_content(data)

        payload_attempts: list[dict[str, Any]] = [payload]

        # GPT-5 can return an empty message.content while still charging reasoning tokens.
        # Best-effort retry once with minimal reasoning effort + slightly larger token budget.
        if not text and model.lower().startswith("gpt-5"):
            retry_payload = dict(payload)
            retry_payload["reasoning_effort"] = "minimal"
            retry_payload["max_completion_tokens"] = max(
                int(retry_payload.get("max_completion_tokens") or 0),
                int(request.max_output_tokens) + 1024,
            )
            payload_attempts.append(retry_payload)
            data = _post_and_parse(retry_payload)
            text = _extract_message_content(data)

        usage_any = data.get("usage")
        usage_raw: dict[str, Any] = dict(usage_any) if isinstance(usage_any, dict) else {}

        if not text:
            completion_details = usage_raw.get("completion_tokens_details")
            snippet = {
                "model": data.get("model"),
                "finish_reason": (data.get("choices") or [{}])[0].get("finish_reason"),
                "usage": {
                    "prompt_tokens": usage_raw.get("prompt_tokens"),
                    "completion_tokens": usage_raw.get("completion_tokens"),
                    "total_tokens": usage_raw.get("total_tokens"),
                    "completion_tokens_details": completion_details,
                },
            }
            raise AiProviderError(
                "OpenAI returned empty message.content. "
                f"Response snippet: {json.dumps(snippet, ensure_ascii=False)}"
            )
        usage = AiUsage(
            input_tokens=usage_raw.get("prompt_tokens"),
            output_tokens=usage_raw.get("completion_tokens"),
            total_tokens=usage_raw.get("total_tokens"),
        )

        return AiResponse(
            text=str(text or ""),
            provider="openai",
            model=str(data.get("model") or request.model),
            usage=usage,
            raw={
                **data,
                "_xscanner": {
                    "request_url": url,
                    "request_payload": _sanitize_payload_for_trace(payload_attempts[-1]),
                    "request_attempts": [_sanitize_payload_for_trace(p) for p in payload_attempts],
                },
            },
        )
