# Why Runtime Introspection > MCP Prompts

This document explains why `nucleai` uses **runtime introspection** instead of **Model Context Protocol (MCP)** for agent interaction.

## TL;DR

Runtime introspection via `help()` is:
- ✅ **Simpler**: No external protocols or servers
- ✅ **Always current**: Documentation lives in code
- ✅ **Universal**: Works with any AI tool
- ✅ **Testable**: Examples in docstrings are validated
- ✅ **Discoverable**: Standard Python patterns

MCP is great for **external tools and data sources**, but for **library code**, introspection wins.

## Comparison

| Aspect | Runtime Introspection | MCP Prompts |
|--------|----------------------|-------------|
| **Setup** | `import nucleai; help(nucleai)` | Configure MCP server, client, prompts |
| **Dependencies** | Python stdlib only | MCP protocol, server, transport layer |
| **Maintenance** | Docstrings in code | Separate prompt files, schemas |
| **Versioning** | Automatic (in code) | Manual synchronization needed |
| **Discoverability** | `list_capabilities()`, `help()` | MCP server listing, prompt catalog |
| **Examples** | In docstrings, tested | In prompt descriptions, may drift |
| **Type Safety** | Python type annotations | JSON schemas, may diverge |
| **Tool Support** | Any Python REPL/IDE | MCP-compatible clients only |
| **Debugging** | Standard Python debugging | MCP protocol debugging |
| **Learning Curve** | Familiar Python patterns | New protocol to learn |

## When to Use Each

### Use Runtime Introspection (like nucleai) When:

✅ Building a **Python library** that AI agents will use
✅ Code is the source of truth
✅ Want to minimize external dependencies
✅ Need examples to be testable and validated
✅ Target multiple AI tools (Claude, GPT, local models)
✅ Developers already know Python

### Use MCP When:

✅ Connecting to **external services** (databases, APIs, file systems)
✅ Need **cross-language** tool definitions
✅ Building **standalone tools** not tied to a specific codebase
✅ Want **centralized tool management** across projects
✅ Need **capability negotiation** between client and server
✅ Implementing **stateful tools** with sessions

## Real-World Example

### MCP Approach (More Complex)

```yaml
# prompts/query_simdb.yaml
name: query_simdb
description: Query ITER SimDB for simulations
arguments:
  - name: constraints
    type: object
    description: Filter constraints
  - name: limit
    type: integer
    description: Max results
```

```python
# Separate MCP server needed
# Separate schema definitions
# Client needs MCP protocol support
# Updates require updating YAML and code
```

### Introspection Approach (Simpler)

```python
# Everything in one place - the code itself
async def query(
    constraints: dict[str, str],
    limit: int = 10
) -> list[Simulation]:
    """Query ITER SimDB for simulations.
    
    Args:
        constraints: Filter constraints (e.g., {'machine': 'ITER'})
        limit: Maximum results to return
    
    Examples:
        >>> results = await query({'machine': 'ITER'}, limit=5)
        >>> for sim in results:
        ...     print(sim.alias)
    """
    # Implementation
```

Agent usage:
```python
# Discovery
help(nucleai.simdb.query)  # See everything above

# Introspection
sig = get_function_signature(nucleai.simdb.query)
# Returns: {'parameters': {'constraints': 'dict[str, str]', ...}, ...}

# Direct use
results = await nucleai.simdb.query({'machine': 'ITER'})
```

## Hybrid Approach

You can combine both:

```python
# Use introspection for your library code
import nucleai
help(nucleai.simdb.query)

# Use MCP for external services
# (e.g., MCP server for database access)
from mcp import use_tool
db_results = await use_tool("database", "query", {...})
```

## Best Practices

### For Library Authors (like nucleai):

1. **Write comprehensive docstrings** with examples
2. **Use Pydantic** for schema validation and JSON schema
3. **Provide introspection utilities** (`get_function_signature`, etc.)
4. **Include `list_capabilities()`** for discovery
5. **Add recovery hints** to exceptions
6. **Test docstring examples** with pytest --doctest-modules

### For Tool Builders:

1. **Use MCP** if your tool is external to the codebase
2. **Expose your MCP tools** through a server
3. **Document in both** MCP prompts and code docstrings
4. **Keep schemas synchronized** between MCP and code

## Migration Path

If you started with MCP and want to move to introspection:

1. **Add comprehensive docstrings** to all functions
2. **Create Pydantic models** for data structures
3. **Add introspection utilities** (copy from nucleai)
4. **Write tests** for docstring examples
5. **Update agent instructions** to use `help()`
6. **Deprecate MCP prompts** gradually

## Conclusion

**For Python libraries**, runtime introspection is simpler, more maintainable, and universally accessible. The code itself becomes the documentation and interface specification.

**For external tools and services**, MCP provides valuable abstractions and protocol negotiation.

Choose the right tool for the job:
- **Library code** → Runtime introspection
- **External services** → MCP
- **Complex systems** → Both (hybrid)

## Additional Reading

- [Python's `help()` function](https://docs.python.org/3/library/functions.html#help)
- [Pydantic JSON Schema](https://docs.pydantic.dev/latest/concepts/json_schema/)
- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
- [nucleai AGENT_QUICKSTART.md](../AGENT_QUICKSTART.md)
