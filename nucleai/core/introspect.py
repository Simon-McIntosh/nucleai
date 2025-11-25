"""Runtime introspection utilities for AI agents.

This module provides tools that enable AI agents to discover and understand
nucleai's capabilities through runtime introspection. Agents can use these
functions to explore available modules, inspect function signatures, and
extract schema information.

Functions:
    get_function_signature: Extract complete function signature
    list_module_functions: List all public functions in a module
    get_model_schema: Get JSON schema from Pydantic model
    discover_capabilities: List all available nucleai capabilities

Examples:
    >>> from nucleai.core.introspect import list_module_functions
    >>> import nucleai.core.models
    >>> functions = list_module_functions(nucleai.core.models)
    >>> print(functions)
    ['CodeInfo', 'Simulation', 'QueryConstraint', ...]

    >>> from nucleai.core.introspect import get_function_signature
    >>> from nucleai.core.config import get_settings
    >>> sig = get_function_signature(get_settings)
    >>> print(sig['returns'])
    Settings
"""

import inspect
from collections.abc import Callable
from typing import Any

import pydantic


def get_function_signature(func: Callable) -> dict[str, Any]:
    """Get machine-readable function signature.

    Extracts complete signature information including parameters, return type,
    and docstring. Useful for AI agents to understand function contracts.

    Args:
        func: Function to introspect

    Returns:
        Dictionary with keys:
            - name: Function name
            - module: Module name
            - parameters: Dict mapping parameter names to type annotations
            - returns: Return type annotation as string
            - docstring: Full docstring text

    Examples:
        >>> from nucleai.core.config import get_settings
        >>> sig = get_function_signature(get_settings)
        >>> print(sig['name'])
        get_settings
        >>> print(sig['returns'])
        Settings
        >>> print('simdb_username' in sig['docstring'])
        True
    """
    sig = inspect.signature(func)
    return {
        "name": func.__name__,
        "module": func.__module__,
        "parameters": {
            name: str(param.annotation) if param.annotation != inspect.Parameter.empty else "Any"
            for name, param in sig.parameters.items()
        },
        "returns": (
            str(sig.return_annotation)
            if sig.return_annotation != inspect.Signature.empty
            else "Any"
        ),
        "docstring": inspect.getdoc(func) or "",
    }


def list_module_functions(module: Any) -> list[str]:
    """List all public functions in a module.

    Returns names of all public callables (functions and classes) that don't
    start with underscore. Useful for discovering module capabilities.

    Args:
        module: Module to introspect

    Returns:
        List of public function and class names

    Examples:
        >>> import nucleai.core.models
        >>> functions = list_module_functions(nucleai.core.models)
        >>> 'Simulation' in functions
        True
        >>> 'CodeInfo' in functions
        True
        >>> '__init__' in functions
        False
    """
    return [
        name for name in dir(module) if not name.startswith("_") and callable(getattr(module, name))
    ]


def get_model_schema(model: type[pydantic.BaseModel]) -> dict[str, Any]:
    """Get JSON schema from Pydantic model.

    Extracts JSON schema representation of a Pydantic model, including field
    types, descriptions, and validation constraints.

    Args:
        model: Pydantic model class

    Returns:
        JSON schema dictionary

    Examples:
        >>> from nucleai.core.models import Simulation
        >>> schema = get_model_schema(Simulation)
        >>> print(schema['title'])
        Simulation
        >>> 'uuid' in schema['properties']
        True
        >>> 'alias' in schema['properties']
        True
    """
    return model.model_json_schema()


def discover_capabilities() -> dict[str, str]:
    """List all available nucleai capabilities.

    Returns mapping of capability names to their module paths. Agents can
    use this to discover what nucleai can do.

    Returns:
        Dictionary mapping capability names to module paths

    Examples:
        >>> from nucleai.core.introspect import discover_capabilities
        >>> caps = discover_capabilities()
        >>> 'simdb' in caps
        True
        >>> caps['simdb']
        'nucleai.simdb'
        >>> caps['embeddings']
        'nucleai.embeddings'
    """
    return {
        "core": "nucleai.core",
        "simdb": "nucleai.simdb",
        "embeddings": "nucleai.embeddings",
        "search": "nucleai.search",
        "features": "nucleai.features",
        "plot": "nucleai.plot",
        "data": "nucleai.data",
    }
