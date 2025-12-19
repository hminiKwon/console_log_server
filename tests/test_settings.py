from __future__ import annotations

import pytest

from console_log_server.core.settings import Settings, get_settings


@pytest.fixture(autouse=True)
def clear_settings_cache() -> None:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_settings_defaults() -> None:
    settings = get_settings()

    assert isinstance(settings, Settings)
    assert settings.host == "127.0.0.1"
    assert settings.port == 8000
    assert settings.debug is False
    assert settings.ollama_instruct_model == "qwen3:1.7b"
    assert settings.ollama_thinking_model == "qwen3-vl:30b"


def test_settings_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CONSOLE_LOG_SERVER_HOST", "0.0.0.0")
    monkeypatch.setenv("CONSOLE_LOG_SERVER_PORT", "9001")
    monkeypatch.setenv("CONSOLE_LOG_SERVER_DEBUG", "true")
    monkeypatch.setenv(
        "CONSOLE_LOG_SERVER_OLLAMA_INSTRUCT_MODEL", "qwen3:1.7b"
    )
    monkeypatch.setenv(
        "CONSOLE_LOG_SERVER_OLLAMA_THINKING_MODEL", "qwen3-vl:30b"
    )

    settings = get_settings()

    assert settings.host == "0.0.0.0"
    assert settings.port == 9001
    assert settings.debug is True
    assert settings.ollama_instruct_model == "qwen3:1.7b"
    assert settings.ollama_thinking_model == "qwen3-vl:30b"
