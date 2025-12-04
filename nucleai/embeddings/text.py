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


async def generate_batch_embeddings(texts: list[str], batch_size: int = 100) -> list[list[float]]:
    """Generate embeddings for multiple texts in batched API calls.

    Processes texts in batches to minimize API round-trips while respecting
    API limits. Much faster than calling generate_text_embedding in a loop.

    Args:
        texts: List of texts to embed (each must be non-empty)
        batch_size: Number of texts per API call (default 100, max 2048)

    Returns:
        List of embedding vectors in same order as input texts

    Raises:
        ValueError: If texts is empty or contains empty strings
        EmbeddingError: If embedding generation fails

    Examples:
        >>> texts = ["ITER baseline scenario", "DINA simulation", "H-mode plasma"]
        >>> embeddings = await generate_batch_embeddings(texts)
        >>> len(embeddings) == len(texts)
        True
        >>> all(len(e) == 1536 for e in embeddings)
        True
    """
    if not texts:
        raise ValueError("texts list cannot be empty")

    # Validate all texts are non-empty
    for i, text in enumerate(texts):
        if not text or not text.strip():
            raise ValueError(f"text at index {i} cannot be empty or whitespace")

    settings = get_settings()
    client = create_embedding_client()

    all_embeddings: list[list[float]] = []

    # Process in batches
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]

        try:
            response = await client.embeddings.create(
                input=batch,
                model=settings.embedding_model,
                dimensions=settings.embedding_dimensions,
            )
            # Extract embeddings in order (API returns in same order as input)
            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)

        except Exception as e:
            raise EmbeddingError(
                f"Failed to generate batch embeddings (batch starting at {i}): {e}",
                recovery_hint="Check OPENAI_API_KEY and network connection",
            ) from e

    return all_embeddings
