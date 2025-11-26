"""Tests for core.config module."""

import pytest
from pydantic import ValidationError

from nucleai.core.config import Settings, get_settings


def test_settings_loads_from_env(temp_env):
    """Test that settings load from environment."""
    settings = Settings()
    assert settings.simdb_username == temp_env["SIMDB_USERNAME"]
    assert settings.simdb_password == temp_env["SIMDB_PASSWORD"]
    assert settings.openai_api_key == temp_env["OPENAI_API_KEY"]


def test_settings_default_values(temp_env):
    """Test default configuration values."""
    settings = Settings()
    assert settings.simdb_remote_url == "https://test.simdb.example.com/api"
    assert settings.embedding_model == "test/embedding-model"
    assert settings.llm_temperature == 0.5


def test_get_settings_caching(temp_env):
    """Test that get_settings returns cached instance."""
    # Clear cache first
    get_settings.cache_clear()

    settings1 = get_settings()
    settings2 = get_settings()
    assert settings1 is settings2


def test_settings_validation_embedding_dimensions(temp_env, monkeypatch):
    """Test validation of embedding dimensions."""
    monkeypatch.setenv("EMBEDDING_DIMENSIONS", "-1")
    with pytest.raises(ValidationError):
        Settings()


def test_settings_validation_temperature(temp_env, monkeypatch):
    """Test validation of LLM temperature."""
    monkeypatch.setenv("LLM_TEMPERATURE", "5.0")
    with pytest.raises(ValidationError):
        Settings()


def test_settings_missing_required_fields(tmp_path, monkeypatch):
    """Test that missing required fields raise validation error."""
    # Point to non-existent .env file to prevent loading from project .env
    monkeypatch.chdir(tmp_path)

    # Remove required fields
    monkeypatch.delenv("SIMDB_USERNAME", raising=False)
    monkeypatch.delenv("SIMDB_PASSWORD", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(ValidationError) as exc_info:
        Settings()

    # Verify the error mentions missing fields
    errors = exc_info.value.errors()
    missing_fields = {err["loc"][0] for err in errors if err["type"] == "missing"}
    assert "simdb_username" in missing_fields
    assert "simdb_password" in missing_fields
    assert "OPENAI_API_KEY" in missing_fields
