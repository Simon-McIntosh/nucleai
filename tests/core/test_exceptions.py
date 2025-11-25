"""Tests for core.exceptions module."""

import pytest

from nucleai.core.exceptions import (
    AuthenticationError,
    ConnectionError,
    EmbeddingError,
    NucleaiError,
    ValidationError,
)


def test_nucleai_error_has_recovery_hint():
    """Test that NucleaiError includes recovery hint."""
    error = NucleaiError("Test error", recovery_hint="Check configuration")
    assert error.recovery_hint == "Check configuration"
    assert str(error) == "Test error"


def test_authentication_error_inheritance():
    """Test AuthenticationError inherits from NucleaiError."""
    error = AuthenticationError("Auth failed", recovery_hint="Check credentials")
    assert isinstance(error, NucleaiError)
    assert error.recovery_hint == "Check credentials"


def test_connection_error():
    """Test ConnectionError creation and attributes."""
    error = ConnectionError("Connection failed", recovery_hint="Check network")
    assert str(error) == "Connection failed"
    assert error.recovery_hint == "Check network"


def test_validation_error():
    """Test ValidationError creation."""
    error = ValidationError("Invalid data", recovery_hint="Check schema")
    assert isinstance(error, NucleaiError)


def test_embedding_error():
    """Test EmbeddingError creation."""
    error = EmbeddingError("Embedding failed", recovery_hint="Check API key")
    assert isinstance(error, NucleaiError)


def test_exception_can_be_raised_and_caught():
    """Test exceptions can be raised and caught."""
    with pytest.raises(AuthenticationError) as exc_info:
        raise AuthenticationError("Test", recovery_hint="Fix it")
    assert exc_info.value.recovery_hint == "Fix it"
