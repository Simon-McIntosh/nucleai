# GitHub Copilot Instructions for nucleai

## Core Principle

This library uses runtime introspection. Use `get_docstring()` for non-interactive documentation access.

## Quick Start

```python
from nucleai.core.introspect import get_docstring, get_function_signature

# Discover capabilities
import nucleai
print(get_docstring(nucleai))

# Explore a module
import nucleai.simdb
print(get_docstring(nucleai.simdb.query))  # See examples and parameters

# Get detailed signatures
sig = get_function_signature(nucleai.simdb.query)
print(sig['docstring'])  # Full docstring
print(sig['parameters'])  # Parameter types
```

## Development Standards

- Use `uv run` for all Python commands
- Python 3.13 with modern syntax (`list[str]` not `List[str]`)
- Async with `anyio`, not asyncio
- Pydantic for schemas
- Test coverage target: 100%

## Configuration

Settings are loaded from `.env`:
```python
from nucleai.core.introspect import get_docstring
from nucleai.core.config import Settings, get_settings

# See documentation
print(get_docstring(get_settings))

# See all required environment variables
schema = Settings.model_json_schema()
print(f"Required fields: {schema['required']}")
```

## Complete Documentation

See these files for full documentation:
- `AGENT_QUICKSTART.md` - Quick start guide for agents
- `AGENTS.md` - Complete development guidelines
- `docs/INTROSPECTION_VS_MCP.md` - Why introspection over MCP
