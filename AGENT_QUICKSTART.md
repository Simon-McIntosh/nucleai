# Agent Quick Start - nucleai

**For AI Agents**: This guide teaches you how to discover and use nucleai through runtime introspection.

## 🚀 Quick Discovery

```python
from nucleai.core.introspect import get_docstring, discover_capabilities

# Step 1: What can nucleai do?
import nucleai
print(get_docstring(nucleai))
caps = discover_capabilities()

# Step 2: Explore a capability
import nucleai.simdb
print(get_docstring(nucleai.simdb))

# Step 3: Use a function (copy example from docstring)
results = await nucleai.simdb.query({'machine': 'ITER'}, limit=5)
```

## 🎯 The Pattern

This codebase uses **self-documenting code** - everything you need is in docstrings:

1. **`get_docstring(module)`** → Read what a module does (non-interactive)
2. **`get_docstring(function)`** → Get usage examples and parameter docs
3. **Copy examples** → All docstring examples are executable
4. **Check exceptions** → Every error has a `recovery_hint` attribute

## 📚 Core Capabilities

| Module | Purpose | Start Here |
|--------|---------|------------|
| `nucleai.core` | Data models, config, introspection | `get_docstring(nucleai.core.models)` |
| `nucleai.simdb` | Query ITER simulation database | `get_docstring(nucleai.simdb.query)` |
| `nucleai.embeddings` | Generate vector embeddings | `get_docstring(nucleai.embeddings.text)` |
| `nucleai.search` | Semantic search with ChromaDB | `get_docstring(nucleai.search.semantic_search)` |
| `nucleai.features` | Extract features from IDS data | (Coming soon) |

## 🔍 Introspection Tools

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

## ⚙️ Configuration

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

## 🐛 Debugging

All exceptions include recovery hints:

```python
try:
    results = await nucleai.simdb.query({'machine': 'ITER'})
except Exception as e:
    if hasattr(e, 'recovery_hint'):
        print(f"How to fix: {e.recovery_hint}")
```

## 💡 Pro Tips

- **Always read docstrings first** - Use `get_docstring()` for non-interactive access
- **Examples are executable** - Copy them directly from docstrings
- **Types are accurate** - Trust the type annotations
- **Schemas are introspectable** - Use `model_json_schema()` for Pydantic models
- **Settings are documented** - Use `Settings.model_json_schema()` to see all options

## 📖 Full Documentation

See `AGENTS.md` for complete agent guidelines including:
- Development setup
- Testing philosophy
- Python style guide
- Async patterns
- Error handling

## 🎓 Learning Path

1. Read `get_docstring(nucleai)` - Understand the overview
2. Explore `nucleai.core.models` - Learn the data structures
3. Try `nucleai.simdb.query` - Query real data
4. Use `nucleai.search.semantic_search` - Find similar items
5. Build custom workflows - Combine capabilities

**Remember**: The code documents itself. When in doubt, use `get_docstring()`!
