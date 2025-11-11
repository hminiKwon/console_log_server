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


def test_settings_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CONSOLE_LOG_SERVER_HOST", "0.0.0.0")
    monkeypatch.setenv("CONSOLE_LOG_SERVER_PORT", "9001")
    monkeypatch.setenv("CONSOLE_LOG_SERVER_DEBUG", "true")

    settings = get_settings()

    assert settings.host == "0.0.0.0"
    assert settings.port == 9001
    assert settings.debug is True
