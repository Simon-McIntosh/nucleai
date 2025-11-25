"""Tests for core.introspect module."""

import nucleai.core.models
from nucleai.core.config import get_settings
from nucleai.core.introspect import (
    discover_capabilities,
    get_function_signature,
    get_model_schema,
    list_module_functions,
)
from nucleai.core.models import Simulation


def test_get_function_signature():
    """Test extracting function signature."""
    sig = get_function_signature(get_settings)
    assert sig["name"] == "get_settings"
    assert "nucleai.core.config" in sig["module"]
    assert "Settings" in sig["returns"]
    assert "Settings" in sig["docstring"]


def test_get_function_signature_with_parameters():
    """Test extracting signature with parameters."""

    def sample_func(x: int, y: str = "default") -> bool:
        """Sample function."""
        return True

    sig = get_function_signature(sample_func)
    assert sig["name"] == "sample_func"
    assert "x" in sig["parameters"]
    assert "int" in sig["parameters"]["x"]
    assert "str" in sig["parameters"]["y"]
    assert "bool" in sig["returns"]


def test_list_module_functions():
    """Test listing module functions."""
    functions = list_module_functions(nucleai.core.models)
    assert "CodeInfo" in functions
    assert "Simulation" in functions
    assert "QueryConstraint" in functions
    # Should not include private methods
    assert not any(name.startswith("_") for name in functions)


def test_get_model_schema():
    """Test getting Pydantic model schema."""
    schema = get_model_schema(Simulation)
    assert "properties" in schema
    assert "uuid" in schema["properties"]
    assert "alias" in schema["properties"]
    assert "title" in schema
    assert schema["title"] == "Simulation"


def test_discover_capabilities():
    """Test discovering nucleai capabilities."""
    caps = discover_capabilities()
    assert isinstance(caps, dict)
    assert "core" in caps
    assert "simdb" in caps
    assert "embeddings" in caps
    assert "search" in caps
    assert caps["core"] == "nucleai.core"
    assert caps["simdb"] == "nucleai.simdb"
