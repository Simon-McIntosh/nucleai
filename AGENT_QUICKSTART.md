# Agent Quick Start - nucleai

**For AI Agents**: This guide teaches you how to discover and use nucleai through runtime introspection.

## 🚀 Quick Discovery

```python
import nucleai

# Step 1: What can nucleai do?
help(nucleai)
caps = nucleai.list_capabilities()

# Step 2: Explore a capability
import nucleai.simdb
help(nucleai.simdb)

# Step 3: Use a function (copy example from docstring)
results = await nucleai.simdb.query({'machine': 'ITER'}, limit=5)
```

## 🎯 The Pattern

This codebase uses **self-documenting code** - everything you need is in docstrings:

1. **`help(module)`** → Read what a module does
2. **`help(function)`** → Get usage examples and parameter docs
3. **Copy examples** → All docstring examples are executable
4. **Check exceptions** → Every error has a `recovery_hint` attribute

## 📚 Core Capabilities

| Module | Purpose | Start Here |
|--------|---------|------------|
| `nucleai.core` | Data models, config, introspection | `help(nucleai.core.models)` |
| `nucleai.simdb` | Query ITER simulation database | `help(nucleai.simdb.query)` |
| `nucleai.embeddings` | Generate vector embeddings | `help(nucleai.embeddings.text)` |
| `nucleai.search` | Semantic search with ChromaDB | `help(nucleai.search.semantic_search)` |
| `nucleai.features` | Extract features from IDS data | (Coming soon) |

## 🔍 Introspection Tools

```python
from nucleai.core.introspect import (
    get_function_signature,  # Get function details
    list_module_functions,   # List module contents
    get_model_schema,        # Get Pydantic schema
    discover_capabilities    # List all modules
)

# Example: Understand a function
sig = get_function_signature(nucleai.simdb.query)
print(f"Name: {sig['name']}")
print(f"Parameters: {sig['parameters']}")
print(f"Returns: {sig['returns']}")
```

## ⚙️ Configuration

```python
from nucleai.core.config import get_settings
help(get_settings)  # See required environment variables

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

- **Always read docstrings first** - `help()` is your friend
- **Examples are executable** - Copy them directly
- **Types are accurate** - Trust the type annotations
- **Schemas are introspectable** - Use `model_json_schema()`
- **Settings are documented** - Check `.env.example`

## 📖 Full Documentation

See `AGENTS.md` for complete agent guidelines including:
- Development setup
- Testing philosophy
- Python style guide
- Async patterns
- Error handling

## 🎓 Learning Path

1. Read `help(nucleai)` - Understand the overview
2. Explore `nucleai.core.models` - Learn the data structures
3. Try `nucleai.simdb.query` - Query real data
4. Use `nucleai.search.semantic_search` - Find similar items
5. Build custom workflows - Combine capabilities

**Remember**: The code documents itself. When in doubt, use `help()`!
