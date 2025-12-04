"""Application configuration management.

This module handles all configuration through environment variables using
pydantic-settings and python-dotenv. Settings are loaded from .env file
and cached for efficient access.

Classes:
    Settings: Application settings loaded from environment

Functions:
    get_settings: Get cached settings instance

Environment Variables:
    SIMDB_USERNAME: ITER username for SimDB authentication
    SIMDB_PASSWORD: ITER password for SimDB authentication
    SIMDB_REMOTE_URL: SimDB API endpoint URL
    SIMDB_REMOTE_NAME: SimDB remote name
    OPENAI_API_KEY: API key for OpenAI-compatible service (e.g., OpenRouter)
    OPENAI_BASE_URL: Base URL for OpenAI-compatible API
    EMBEDDING_MODEL: Embedding model name
    EMBEDDING_DIMENSIONS: Embedding vector dimensions
    LLM_MODEL: LLM model name for code generation
    LLM_TEMPERATURE: LLM temperature (0.0-1.0)
    LLM_MAX_TOKENS: Maximum tokens for LLM responses
    CHROMADB_PATH: Path to ChromaDB storage directory
    CHROMADB_COLLECTION_NAME: ChromaDB collection name
    LOG_LEVEL: Logging level (DEBUG, INFO, WARNING, ERROR)

Examples:
    >>> from nucleai.core.config import get_settings
    >>> settings = get_settings()
    >>> print(settings.simdb_username)
    your_iter_username
    >>> print(settings.openai_api_key[:10] + '...')
    sk-or-v1-c...
    >>> print(settings.embedding_model)
    openai/text-embedding-3-small
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment.

    All settings are loaded from environment variables or .env file.
    Use get_settings() to access a cached instance.

    Attributes:
        simdb_username: ITER username for authentication
        simdb_password: ITER password for authentication
        simdb_remote_url: SimDB API endpoint
        simdb_remote_name: SimDB remote identifier
        openai_api_key: API key for OpenAI-compatible service
        openai_base_url: Base URL for OpenAI-compatible API
        embedding_model: Model for generating embeddings
        embedding_dimensions: Dimension of embedding vectors
        llm_model: LLM model for code generation
        llm_temperature: Temperature for LLM sampling
        llm_max_tokens: Maximum tokens in LLM responses
        chromadb_path: Path to ChromaDB database
        chromadb_collection_name: Collection name in ChromaDB
        log_level: Application logging level

    Examples:
        >>> settings = Settings()
        >>> print(settings.simdb_username)
        your_iter_username
        >>> print(settings.model_dump())
        {'simdb_username': 'your_iter_username', ...}
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    # SimDB Configuration
    simdb_username: str
    simdb_password: str
    simdb_remote_url: str = "https://simdb.iter.org/scenarios/api"
    simdb_remote_name: str = "iter"

    # OpenAI-compatible API Configuration (e.g., OpenRouter)
    openai_api_key: str = Field(alias="OPENAI_API_KEY")
    openai_base_url: str = Field(default="https://openrouter.ai/api/v1", alias="OPENAI_BASE_URL")

    # Embedding Configuration
    embedding_model: str = "openai/text-embedding-3-small"
    embedding_dimensions: int = Field(default=1536, gt=0)

    # LLM Configuration
    llm_model: str = "anthropic/claude-3.5-sonnet"
    llm_temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    llm_max_tokens: int = Field(default=4096, gt=0)

    # Logging
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    Settings are loaded once and cached for the application lifetime.
    Environment variables are read from .env file if present.

    Returns:
        Cached Settings instance

    Raises:
        ValidationError: If required environment variables are missing

    Examples:
        >>> from nucleai.core.config import get_settings
        >>> settings = get_settings()
        >>> print(settings.simdb_username)
        your_iter_username

        >>> # Settings are cached - same instance returned
        >>> settings2 = get_settings()
        >>> assert settings is settings2
    """
    return Settings()
