"""Text embedding generation using OpenRouter.

Functions:
    generate_text_embedding: Generate vector embedding for text
    create_embedding_client: Create configured OpenAI client

Examples:
    >>> from nucleai.embeddings.text import generate_text_embedding
    >>> embedding = await generate_text_embedding("ITER baseline scenario")
    >>> assert isinstance(embedding, list)
    >>> assert all(isinstance(x, float) for x in embedding)
"""

from openai import AsyncOpenAI

from nucleai.core.config import get_settings
from nucleai.core.exceptions import EmbeddingError


def create_embedding_client() -> AsyncOpenAI:
    """Create OpenAI client configured for OpenRouter.

    Returns:
        Configured AsyncOpenAI client

    Examples:
        >>> from nucleai.embeddings.text import create_embedding_client
        >>> client = create_embedding_client()
        >>> assert client.base_url is not None
    """
    settings = get_settings()
    return AsyncOpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)


async def generate_text_embedding(text: str) -> list[float]:
    """Generate vector embedding for text.

    Uses OpenAI embeddings API via OpenRouter to generate semantic vector
    representation of input text.

    Args:
        text: Text to embed (non-empty string)

    Returns:
        List of floats representing embedding vector

    Raises:
        ValueError: If text is empty or whitespace only
        EmbeddingError: If embedding generation fails

    Examples:
        >>> embedding = await generate_text_embedding("ITER baseline scenario")
        >>> len(embedding)
        1536
        >>> all(isinstance(x, float) for x in embedding)
        True

        >>> # Empty text raises error
        >>> try:
        ...     await generate_text_embedding("")
        ... except ValueError as e:
        ...     print("Empty text not allowed")
        Empty text not allowed
    """
    if not text or not text.strip():
        raise ValueError("text cannot be empty or whitespace")

    settings = get_settings()
    client = create_embedding_client()

    try:
        response = await client.embeddings.create(
            input=text, model=settings.embedding_model, dimensions=settings.embedding_dimensions
        )
        return response.data[0].embedding

    except Exception as e:
        raise EmbeddingError(
            f"Failed to generate embedding: {e}",
            recovery_hint="Check OPENAI_API_KEY and network connection",
        ) from e
