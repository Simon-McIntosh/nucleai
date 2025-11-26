"""Tests for embeddings.text module."""

import pytest
from openai import AsyncOpenAI

from nucleai.core.exceptions import EmbeddingError
from nucleai.embeddings.text import create_embedding_client, generate_text_embedding


class TestCreateEmbeddingClient:
    """Tests for create_embedding_client function."""

    def test_creates_openai_client(self):
        """Test that client is created with correct configuration."""
        client = create_embedding_client()

        assert isinstance(client, AsyncOpenAI)
        assert client.api_key is not None
        assert client.base_url is not None

    def test_uses_settings_configuration(self, monkeypatch):
        """Test that client uses settings for configuration."""
        # Mock settings to verify they're used
        monkeypatch.setenv("OPENAI_API_KEY", "test-key-123")
        monkeypatch.setenv("OPENAI_BASE_URL", "https://test.example.com/v1")

        # Clear settings cache to pick up new env vars
        from nucleai.core.config import get_settings

        get_settings.cache_clear()

        client = create_embedding_client()

        assert client.api_key == "test-key-123"
        assert "test.example.com" in str(client.base_url)

        # Clean up
        get_settings.cache_clear()


class TestGenerateTextEmbedding:
    """Tests for generate_text_embedding function."""

    async def test_rejects_empty_string(self):
        """Test that empty string raises ValueError."""
        with pytest.raises(ValueError, match="text cannot be empty"):
            await generate_text_embedding("")

    async def test_rejects_whitespace_only(self):
        """Test that whitespace-only string raises ValueError."""
        with pytest.raises(ValueError, match="text cannot be empty"):
            await generate_text_embedding("   \n\t  ")

    async def test_successful_embedding_generation(self, mocker):
        """Test successful embedding generation."""
        # Mock the OpenAI client
        mock_response = mocker.Mock()
        mock_response.data = [mocker.Mock(embedding=[0.1, 0.2, 0.3] * 512)]

        mock_client = mocker.Mock(spec=AsyncOpenAI)
        mock_client.embeddings.create = mocker.AsyncMock(return_value=mock_response)

        mocker.patch("nucleai.embeddings.text.create_embedding_client", return_value=mock_client)

        embedding = await generate_text_embedding("test text")

        assert isinstance(embedding, list)
        assert len(embedding) == 1536
        assert all(isinstance(x, float) for x in embedding)

        # Verify API was called correctly
        mock_client.embeddings.create.assert_called_once()
        call_kwargs = mock_client.embeddings.create.call_args.kwargs
        assert call_kwargs["input"] == "test text"
        assert "model" in call_kwargs
        assert "dimensions" in call_kwargs

    async def test_api_error_raises_embedding_error(self, mocker):
        """Test that API errors are wrapped in EmbeddingError."""
        mock_client = mocker.Mock(spec=AsyncOpenAI)
        mock_client.embeddings.create = mocker.AsyncMock(
            side_effect=Exception("API connection failed")
        )

        mocker.patch("nucleai.embeddings.text.create_embedding_client", return_value=mock_client)

        with pytest.raises(EmbeddingError, match="Failed to generate embedding"):
            await generate_text_embedding("test text")

    async def test_embedding_error_includes_recovery_hint(self, mocker):
        """Test that EmbeddingError includes recovery hint."""
        mock_client = mocker.Mock(spec=AsyncOpenAI)
        mock_client.embeddings.create = mocker.AsyncMock(side_effect=Exception("API error"))

        mocker.patch("nucleai.embeddings.text.create_embedding_client", return_value=mock_client)

        with pytest.raises(EmbeddingError) as exc_info:
            await generate_text_embedding("test text")

        assert "OPENAI_API_KEY" in exc_info.value.recovery_hint

    async def test_uses_configured_model_and_dimensions(self, mocker):
        """Test that configured model and dimensions are used."""
        mock_response = mocker.Mock()
        mock_response.data = [mocker.Mock(embedding=[0.1] * 1536)]

        mock_client = mocker.Mock(spec=AsyncOpenAI)
        mock_client.embeddings.create = mocker.AsyncMock(return_value=mock_response)

        mocker.patch("nucleai.embeddings.text.create_embedding_client", return_value=mock_client)

        await generate_text_embedding("ITER baseline scenario")

        call_kwargs = mock_client.embeddings.create.call_args.kwargs
        # Verify model and dimensions are passed from settings
        assert call_kwargs["model"] is not None
        assert call_kwargs["dimensions"] > 0
