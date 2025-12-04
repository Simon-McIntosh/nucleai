"""Vector embedding generation for text and images.

This module provides async interfaces for generating embeddings using OpenAI
client configured for OpenRouter. Supports both text and image embeddings.

Modules:
    text: Text embedding generation
    image: Image embedding generation (placeholder)

Environment Variables:
    OPENAI_API_KEY: API key for OpenAI-compatible service
    OPENAI_BASE_URL: Base URL for API (default: https://openrouter.ai/api/v1)
    EMBEDDING_MODEL: Model name (e.g., openai/text-embedding-3-small)

Examples:
    >>> from nucleai.embeddings import generate_text_embedding
    >>> help(generate_text_embedding)

    >>> # Generate embedding for text
    >>> embedding = await generate_text_embedding("Baseline ITER scenario")
    >>> print(len(embedding))
    1536
"""

from nucleai.embeddings.text import generate_batch_embeddings, generate_text_embedding

__all__ = ["generate_text_embedding", "generate_batch_embeddings"]

__agent_exposed__ = True
