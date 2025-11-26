# Agent Quick Start

Runtime introspection guide for AI agents working with nucleai.

## Discovery Pattern

```python
from nucleai.core.introspect import get_docstring, discover_capabilities

# Discover available modules
import nucleai
print(get_docstring(nucleai))
caps = discover_capabilities()

# Explore a module
import nucleai.simdb
print(get_docstring(nucleai.simdb))

# Use a function (examples in docstrings)
results = await nucleai.simdb.query({'machine': 'ITER'})
```

## Core Pattern

All documentation is in docstrings:

1. `get_docstring(obj)` - Read documentation non-interactively
2. Copy examples from docstrings - All examples are tested
3. Use `model_json_schema()` for data structures
4. Exceptions include `recovery_hint` attribute

## SimDB Query Examples

```python
from nucleai.simdb import query, fetch_simulation

# Get all simulations (~1300 records, <2s)
all_sims = await query()  # Defaults to limit=2000

# Filter by machine (exact match)
iter_sims = await query(filters={'machine': 'ITER'})

# Filter by code name (contains)
metis_sims = await query(filters={'code.name': 'in:METIS'})

# Multiple filters (AND logic)
passed = await query(filters={'machine': 'ITER', 'status': 'passed'})

# Find user's latest simulation (in-code filtering)
all_sims = await query()
user_sims = [s for s in all_sims if s.author_email and 'Florian' in s.author_email]
if user_sims:
    latest = max(user_sims, key=lambda s: s.metadata.datetime or '')
    sim = await fetch_simulation(latest.uuid)
    print(sim.imas_uri)
```

### Filter Syntax

- **Exact match**: `{'machine': 'ITER'}`
- **Contains**: `{'code.name': 'in:METIS'}` matches METIS, METIS4IMAS, etc.
- **Multiple**: `{'machine': 'ITER', 'status': 'passed'}` uses AND logic

Available filter fields: `machine`, `status`, `alias`, `code.name`, `uuid`, `description`

## Core Capabilities

| Module | Purpose | Start Here |
|--------|---------|------------|
| `nucleai.core` | Data models, config, introspection | `get_docstring(nucleai.core.models)` |
| `nucleai.simdb` | Query ITER simulation database | `get_docstring(nucleai.simdb.query)` |
| `nucleai.embeddings` | Generate vector embeddings | `get_docstring(nucleai.embeddings.text)` |
| `nucleai.search` | Semantic search with ChromaDB | `get_docstring(nucleai.search.semantic_search)` |
| `nucleai.features` | Extract features from IDS data | (Coming soon) |

## Introspection Tools

```python
from nucleai.core.introspect import (
    get_docstring,           # Get docstring (non-interactive)
    get_function_signature,  # Get function details
    list_module_functions,   # List module contents
    get_model_schema,        # Get Pydantic schema
    discover_capabilities    # List all modules
)

# Example: Read documentation
from nucleai.simdb import query
print(get_docstring(query))

# Example: Understand a function signature
sig = get_function_signature(query)
print(f"Name: {sig['name']}")
print(f"Parameters: {sig['parameters']}")
print(f"Returns: {sig['returns']}")
```

## Configuration

```python
from nucleai.core.introspect import get_docstring
from nucleai.core.config import Settings, get_settings

# See required environment variables
print(get_docstring(get_settings))

# Get full schema with defaults
schema = Settings.model_json_schema()
print(f"Required: {schema['required']}")

# Copy .env.example to .env and configure:
# - SIMDB_USERNAME, SIMDB_PASSWORD
# - OPENROUTER_API_KEY
# - EMBEDDING_MODEL
# - CHROMADB_PATH
```

## Debugging

All exceptions include recovery hints:

```python
try:
    results = await nucleai.simdb.query({'machine': 'ITER'})
except Exception as e:
    if hasattr(e, 'recovery_hint'):
        print(f"How to fix: {e.recovery_hint}")
```

## Key Principles

- Use `get_docstring()` for non-interactive documentation access
- All docstring examples are executable - copy them directly
- Trust type annotations - they are accurate
- Use `model_json_schema()` for Pydantic models
- Configuration is self-documenting via schema

## Full Documentation

See `AGENTS.md` for:
- Development setup and standards
- Testing philosophy
- Python style guide
- Async patterns
- Error handling

The code documents itself through introspection.
