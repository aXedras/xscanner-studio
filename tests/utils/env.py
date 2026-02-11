"""Test helpers for environment setup."""

from __future__ import annotations

from collections.abc import Mapping


def set_required_env(
    monkeypatch,
    *,
    pricing: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Set required config environment variables for tests."""
    env_vars = {
        "OPENAI_API_KEY": "sk-test",
        "OPENAI_MODEL": "gpt-5.2",
        "OPENAI_TEMPERATURE": "0.0",
        "OPENAI_MAX_TOKENS": "16000",
        "OPENAI_MAX_OUTPUT_TOKENS": "900",
        "GOOGLE_API_KEY": "google-test",
        "GOOGLE_MODEL": "gemini-2.0-flash",
        "LORA_BASE_URL": "https://fake.example.com",
        "LORA_SYSTEM_PROMPT_FILE": "config/lora_system_prompt.txt",
        "LORA_USER_PROMPT_FILE": "config/lora_user_prompt_extended.txt",
        "LORA_STAGE1_USER_PROMPT_FILE": "config/lora_user_prompt_extended.txt",
        "LORA_STAGE2_USER_PROMPT_FILE": "config/lora_user_prompt_OCR.txt",
        "CHATGPT_STAGE2_SYSTEM_PROMPT_FILE": "config/system_prompt_image.txt",
        "CHATGPT_STAGE2_USER_PROMPT_FILE": "config/chatgpt_prompt_image.txt",
        "AXEDRAS_BASE_URL": "https://instance1.acc.axedras.io",
        "AXEDRAS_KEYCLOAK_URL": "https://keycloak.acc.axedras.io",
        "AXEDRAS_REALM": "instance1",
        "AXEDRAS_USERNAME": "user",
        "AXEDRAS_PASSWORD": "pass",
        "AXEDRAS_CLIENT_ID": "axedras-api",
        "SERVER_HOST": "0.0.0.0",
        "SERVER_PORT": "8000",
        "SERVER_WORKERS": "4",
        "MAX_TEST_IMAGES": "10",
        "STRATEGY_IMAGE_WORKERS": "0",
    }

    if pricing:
        env_vars.update(pricing)

    for key, val in env_vars.items():
        monkeypatch.setenv(key, val)

    return env_vars
