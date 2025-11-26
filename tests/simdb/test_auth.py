"""Tests for simdb.auth module."""

import os

import pytest

from nucleai.core.config import get_settings
from nucleai.core.exceptions import AuthenticationError
from nucleai.simdb.auth import get_credentials, prepare_env


@pytest.fixture(autouse=True)
def clear_settings_cache():
    """Clear settings cache before and after each test."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_get_credentials_success(temp_env):
    """Test get_credentials with valid environment."""
    username, password = get_credentials()
    assert username == "test_user"
    assert password == "test_password"


def test_get_credentials_empty_username(temp_env, monkeypatch):
    """Test get_credentials raises error when username empty."""
    monkeypatch.setenv("SIMDB_USERNAME", "")

    with pytest.raises(AuthenticationError) as exc_info:
        get_credentials()

    assert "SimDB credentials not found" in str(exc_info.value)
    assert "SIMDB_USERNAME and SIMDB_PASSWORD" in exc_info.value.recovery_hint


def test_get_credentials_empty_password(temp_env, monkeypatch):
    """Test get_credentials raises error when password empty."""
    monkeypatch.setenv("SIMDB_PASSWORD", "")

    with pytest.raises(AuthenticationError) as exc_info:
        get_credentials()

    assert "SimDB credentials not found" in str(exc_info.value)


def test_prepare_env_success(temp_env):
    """Test prepare_env creates environment dict with credentials."""
    env = prepare_env()

    assert isinstance(env, dict)
    assert "SIMDB_USERNAME" in env
    assert "SIMDB_PASSWORD" in env
    assert env["SIMDB_USERNAME"] == "test_user"
    assert env["SIMDB_PASSWORD"] == "test_password"


def test_prepare_env_includes_existing_environment(temp_env, monkeypatch):
    """Test prepare_env includes existing environment variables."""
    monkeypatch.setenv("TEST_VAR", "test_value")

    env = prepare_env()

    assert "TEST_VAR" in env
    assert env["TEST_VAR"] == "test_value"
    assert "SIMDB_USERNAME" in env
    assert "SIMDB_PASSWORD" in env


def test_prepare_env_raises_when_credentials_empty(temp_env, monkeypatch):
    """Test prepare_env raises AuthenticationError when credentials empty."""
    monkeypatch.setenv("SIMDB_PASSWORD", "")

    with pytest.raises(AuthenticationError):
        prepare_env()


def test_prepare_env_makes_copy_of_environment(temp_env):
    """Test that prepare_env returns a copy, not reference to os.environ."""
    env = prepare_env()

    # Modify the returned env
    env["NEW_VAR"] = "new_value"

    # Original os.environ should not be modified
    assert "NEW_VAR" not in os.environ
