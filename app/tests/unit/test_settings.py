"""Settings env-var override tests.

Regression coverage for issue #6: nested settings classes combined
`env_prefix` with field names that already encoded the prefix
(e.g. env_prefix=MONGO_ + field mongo_url -> looked for MONGO_MONGO_URL),
so env-var overrides were silently ignored.
"""

import pytest


@pytest.fixture(autouse=True)
def isolate_env(monkeypatch):
    """Skip .env-file loading so tests only see explicit overrides."""
    monkeypatch.setenv("ENV_FILE", "/nonexistent.env")


def test_mongo_url_env_override(monkeypatch):
    monkeypatch.setenv("MONGO_URL", "mongodb://override.example:27017")
    from app.config.settings import DatabaseSettings
    assert DatabaseSettings().mongo_url == "mongodb://override.example:27017"


def test_redis_url_env_override(monkeypatch):
    monkeypatch.setenv("REDIS_URL", "redis://override.example:6379/1")
    from app.config.settings import RedisSettings
    assert RedisSettings().redis_url == "redis://override.example:6379/1"


def test_api_host_env_override(monkeypatch):
    monkeypatch.setenv("API_HOST", "127.0.0.1")
    from app.config.settings import APISettings
    assert APISettings().api_host == "127.0.0.1"


def test_log_level_env_override(monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    from app.config.settings import LoggingSettings
    assert LoggingSettings().log_level == "DEBUG"


def test_celery_broker_url_env_override(monkeypatch):
    monkeypatch.setenv("CELERY_BROKER_URL", "amqp://override.example:5672//")
    from app.config.settings import CelerySettings
    assert CelerySettings().broker_url == "amqp://override.example:5672//"
