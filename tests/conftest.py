"""Shared test fixtures for nucleai test suite."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def temp_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    """Create temporary environment variables for testing.

    Args:
        tmp_path: Pytest temporary directory fixture
        monkeypatch: Pytest monkeypatch fixture for environment variables

    Returns:
        Dictionary of environment variables set for testing

    Examples:
        >>> def test_config(temp_env):
        ...     assert temp_env["SIMDB_USERNAME"] == "test_user"
    """
    env_vars = {
        "SIMDB_USERNAME": "test_user",
        "SIMDB_PASSWORD": "test_password",
        "SIMDB_REMOTE_URL": "https://test.simdb.example.com/api",
        "SIMDB_REMOTE_NAME": "test_remote",
        "OPENROUTER_API_KEY": "test_api_key",
        "OPENROUTER_BASE_URL": "https://test.openrouter.example.com/v1",
        "EMBEDDING_MODEL": "test/embedding-model",
        "EMBEDDING_DIMENSIONS": "768",
        "LLM_MODEL": "test/llm-model",
        "LLM_TEMPERATURE": "0.5",
        "LLM_MAX_TOKENS": "2048",
        "CHROMADB_PATH": str(tmp_path / "chromadb"),
        "CHROMADB_COLLECTION_NAME": "test_collection",
        "LOG_LEVEL": "DEBUG",
    }

    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)

    return env_vars


@pytest.fixture
def mock_openai_client() -> MagicMock:
    """Create a mock OpenAI client for testing.

    Returns:
        Mock OpenAI client with embeddings.create method

    Examples:
        >>> def test_embedding(mock_openai_client):
        ...     result = mock_openai_client.embeddings.create()
        ...     assert len(result.data[0].embedding) == 768
    """
    mock_client = MagicMock()
    mock_embedding = MagicMock()
    mock_embedding.embedding = [0.1] * 768
    mock_response = MagicMock()
    mock_response.data = [mock_embedding]
    mock_client.embeddings.create.return_value = mock_response
    return mock_client


@pytest.fixture
def sample_simulation_data() -> dict[str, str]:
    """Provide sample simulation metadata for testing.

    Returns:
        Dictionary with simulation fields

    Examples:
        >>> def test_simulation(sample_simulation_data):
        ...     assert sample_simulation_data["machine"] == "ITER"
    """
    return {
        "uuid": "123e4567-e89b-12d3-a456-426614174000",
        "alias": "ITER-001",
        "machine": "ITER",
        "code_name": "METIS",
        "code_version": "1.0.0",
        "description": "Baseline ITER scenario with 15MA plasma current",
        "status": "passed",
    }
