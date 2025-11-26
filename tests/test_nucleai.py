"""Tests for nucleai main module."""

import nucleai
from nucleai import __version__, discover_capabilities, list_capabilities


def test_version_exists():
    """Test that __version__ is defined."""
    assert __version__ is not None
    assert isinstance(__version__, str)
    assert len(__version__) > 0


def test_discover_capabilities():
    """Test discover_capabilities is exported."""
    caps = discover_capabilities()
    assert isinstance(caps, dict)
    assert len(caps) > 0


def test_list_capabilities():
    """Test list_capabilities function."""
    caps = list_capabilities()
    assert isinstance(caps, dict)
    assert len(caps) > 0

    # Check expected capabilities
    assert "core" in caps
    assert caps["core"] == "nucleai.core"


def test_list_capabilities_matches_discover():
    """Test that list_capabilities returns same result as discover_capabilities."""
    list_caps = list_capabilities()
    discover_caps = discover_capabilities()
    assert list_caps == discover_caps


def test_nucleai_module_has_docstring():
    """Test that nucleai module has documentation."""
    assert nucleai.__doc__ is not None
    assert "nucleai" in nucleai.__doc__.lower()


def test_nucleai_exports_expected_symbols():
    """Test that nucleai exports expected public symbols."""
    assert hasattr(nucleai, "__version__")
    assert hasattr(nucleai, "discover_capabilities")
    assert hasattr(nucleai, "list_capabilities")

    # Verify __all__ is defined
    assert hasattr(nucleai, "__all__")
    assert "__version__" in nucleai.__all__
    assert "discover_capabilities" in nucleai.__all__
