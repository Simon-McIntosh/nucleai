"""Custom exception hierarchy with recovery hints for AI agents.

This module defines exceptions specific to nucleai operations. Each exception
includes a recovery hint to help AI agents diagnose and fix issues.

Classes:
    NucleaiError: Base exception with recovery hint
    AuthenticationError: SimDB authentication failure
    ConnectionError: Network or connectivity issue
    ValidationError: Data validation failure
    EmbeddingError: Embedding generation failure

Examples:
    >>> from nucleai.core.exceptions import AuthenticationError
    >>> help(AuthenticationError)
    >>> try:
    ...     raise AuthenticationError(
    ...         "Invalid SimDB credentials",
    ...         recovery_hint="Check SIMDB_USERNAME and SIMDB_PASSWORD in .env"
    ...     )
    ... except AuthenticationError as e:
    ...     print(e.recovery_hint)
    Check SIMDB_USERNAME and SIMDB_PASSWORD in .env
"""


class NucleaiError(Exception):
    """Base exception for all nucleai errors.

    All nucleai exceptions inherit from this class and include a recovery
    hint to help diagnose and fix the issue.

    Attributes:
        message: Error message describing what went wrong
        recovery_hint: Suggestion for how to fix the issue

    Examples:
        >>> error = NucleaiError(
        ...     "Something went wrong",
        ...     recovery_hint="Try checking the logs"
        ... )
        >>> print(error.recovery_hint)
        Try checking the logs
    """

    def __init__(self, message: str, recovery_hint: str) -> None:
        """Initialize nucleai error with recovery hint.

        Args:
            message: Error message
            recovery_hint: Suggestion for fixing the issue
        """
        super().__init__(message)
        self.recovery_hint = recovery_hint


class AuthenticationError(NucleaiError):
    """SimDB authentication failure.

    Raised when SimDB credentials are invalid or missing.

    Examples:
        >>> from nucleai.core.exceptions import AuthenticationError
        >>> raise AuthenticationError(
        ...     "Invalid SimDB credentials",
        ...     recovery_hint="Check SIMDB_USERNAME and SIMDB_PASSWORD in .env"
        ... )
        Traceback (most recent call last):
        ...
        nucleai.core.exceptions.AuthenticationError: Invalid SimDB credentials
    """

    pass


class ConnectionError(NucleaiError):
    """Network or connectivity issue.

    Raised when unable to connect to SimDB, OpenRouter, or other services.

    Examples:
        >>> from nucleai.core.exceptions import ConnectionError
        >>> raise ConnectionError(
        ...     "Unable to connect to SimDB",
        ...     recovery_hint="Check network connection and SIMDB_REMOTE_URL"
        ... )
        Traceback (most recent call last):
        ...
        nucleai.core.exceptions.ConnectionError: Unable to connect to SimDB
    """

    pass


class ValidationError(NucleaiError):
    """Data validation failure.

    Raised when data doesn't match expected schema or constraints.

    Examples:
        >>> from nucleai.core.exceptions import ValidationError
        >>> raise ValidationError(
        ...     "Invalid simulation data format",
        ...     recovery_hint="Check that simulation has required fields: uuid, alias, machine"
        ... )
        Traceback (most recent call last):
        ...
        nucleai.core.exceptions.ValidationError: Invalid simulation data format
    """

    pass


class EmbeddingError(NucleaiError):
    """Embedding generation failure.

    Raised when unable to generate embeddings from text or images.

    Examples:
        >>> from nucleai.core.exceptions import EmbeddingError
        >>> raise EmbeddingError(
        ...     "Failed to generate embedding",
        ...     recovery_hint="Check OPENROUTER_API_KEY and network connection"
        ... )
        Traceback (most recent call last):
        ...
        nucleai.core.exceptions.EmbeddingError: Failed to generate embedding
    """

    pass
