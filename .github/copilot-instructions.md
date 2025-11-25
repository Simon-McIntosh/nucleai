# GitHub Copilot Instructions for nucleai

## Codegen-First Approach

This library is designed for runtime introspection. Always prefer executing code over reading source files.

### Core Principle

Run code to discover what you need, then execute it. Don't read files to understand APIs.

### Workflow

1. Use `get_docstring()` to read documentation
2. Use `model_json_schema()` to discover data structures
3. Copy examples from docstrings
4. Execute code to test

### When to Read Files

Read source files ONLY when:
- Implementing new features
- Modifying existing code
- Debugging implementation details

Never read files for:
- API documentation
- Configuration requirements  
- Usage examples
- Understanding function behavior

## Introspection API

```python
from nucleai.core.introspect import (
    get_docstring,           # Read any docstring
    get_function_signature,  # Get parameter types
    list_module_functions,   # List module contents
    discover_capabilities    # List all modules
)

# For Pydantic models
Model.model_json_schema()  # Get schema with all fields
```

## Development Standards

- Use `uv run` for all Python commands
- Python 3.13+ syntax
- Async with `anyio`
- Pydantic for data models
- Test coverage target: 100%

## Complete Documentation

See these files for full documentation:
- `AGENT_QUICKSTART.md` - Quick start guide for agents
- `AGENTS.md` - Complete development guidelines
- `docs/INTROSPECTION_VS_MCP.md` - Why introspection over MCP
