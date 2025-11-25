"""Authentication management for SimDB.

Handles credential loading from environment and preparation of subprocess
environment for non-interactive SimDB CLI commands.

Functions:
    get_credentials: Load and validate SimDB credentials
    prepare_env: Prepare environment dict for subprocess

Examples:
    >>> from nucleai.simdb.auth import get_credentials
    >>> username, password = get_credentials()
    >>> print(username)
    your_iter_username
"""

import os

from nucleai.core.config import get_settings
from nucleai.core.exceptions import AuthenticationError


def get_credentials() -> tuple[str, str]:
    """Load and validate SimDB credentials from environment.

    Reads credentials from environment variables via settings. Raises
    AuthenticationError if credentials are missing or empty.

    Returns:
        Tuple of (username, password)

    Raises:
        AuthenticationError: If credentials are missing or empty

    Examples:
        >>> from nucleai.simdb.auth import get_credentials
        >>> username, password = get_credentials()
        >>> assert isinstance(username, str)
        >>> assert isinstance(password, str)
        >>> assert len(username) > 0
    """
    settings = get_settings()

    if not settings.simdb_username or not settings.simdb_password:
        raise AuthenticationError(
            "SimDB credentials not found",
            recovery_hint="Set SIMDB_USERNAME and SIMDB_PASSWORD in .env file",
        )

    return settings.simdb_username, settings.simdb_password


def prepare_env() -> dict[str, str]:
    """Prepare environment dictionary for subprocess with credentials.

    Creates environment dict with SimDB credentials for non-interactive
    CLI command execution. Includes all current environment variables
    plus SIMDB_USERNAME and SIMDB_PASSWORD.

    Returns:
        Environment dictionary suitable for subprocess.run(env=...)

    Raises:
        AuthenticationError: If credentials are missing

    Examples:
        >>> from nucleai.simdb.auth import prepare_env
        >>> env = prepare_env()
        >>> assert 'SIMDB_USERNAME' in env
        >>> assert 'SIMDB_PASSWORD' in env
    """
    username, password = get_credentials()

    env = os.environ.copy()
    env["SIMDB_USERNAME"] = username
    env["SIMDB_PASSWORD"] = password

    return env
