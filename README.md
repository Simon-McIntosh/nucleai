# nucleai

**AI Support for Fusion Experiments**

`nucleai` is a codegen-first library designed to empower fusion research with advanced AI capabilities. It provides a comprehensive workflow for extracting features from fusion data, generating rich descriptions, and creating vector embeddings for both feature images and text.

## Key Features

- **Natural Language Interface**: Ask questions about data and test hypotheses using natural language.
- **Data Search & Retrieval**: Advanced search capabilities using text and feature shapes.
- **Analysis & Display**: Automated analysis and visualization of experimental data.
- **Feature Extraction**: Automated extraction of significant features from experimental fusion data.
- **Vector Embeddings**: Generation of embeddings for feature images and text descriptions to enable semantic understanding.
- **Codegen-First Design**: Built to be driven by AI agents and code generation tools, allowing users to request complex, novel plots and processing pipelines on demand.
- **Runtime Introspection**: Comprehensive docstrings enable AI agents to use Python's `help()` system to discover and understand capabilities.

## Getting Started

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/nucleai.git
cd nucleai

# Install with uv
uv sync
```

### Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
# Edit .env with your credentials
```

Required environment variables:
- `SIMDB_USERNAME` - Your ITER username
- `SIMDB_PASSWORD` - Your ITER password  
- `OPENROUTER_API_KEY` - Your OpenRouter API key

### Quick Start

```python
import nucleai

# Discover available capabilities
caps = nucleai.list_capabilities()
for name, module_path in caps.items():
    print(f"{name}: {module_path}")

# Query ITER SimDB
from nucleai.simdb import query
results = await query({'machine': 'ITER'}, limit=5)
for sim in results:
    print(f"{sim.alias}: {sim.code.name}")

# Semantic search
from nucleai.search import semantic_search
results = await semantic_search("baseline ITER scenario", limit=5)
for result in results:
    print(f"{result.id}: {result.similarity:.2f}")
```

## For AI Agents

This library is designed for runtime introspection. Use Python's `help()` system:

```python
import nucleai
help(nucleai)  # Get module overview

import nucleai.simdb
help(nucleai.simdb.query)  # Get function documentation

# Introspect programmatically
from nucleai.core.introspect import get_function_signature
sig = get_function_signature(nucleai.simdb.query)
print(sig['parameters'])  # See parameter types
```

## Architecture

- `nucleai.core` - Core models, configuration, exceptions, introspection
- `nucleai.simdb` - ITER SimDB integration  
- `nucleai.embeddings` - Vector embedding generation (OpenRouter)
- `nucleai.search` - Semantic search (ChromaDB)
- `nucleai.features` - Feature extraction from IDS data
- `nucleai.plot` - Visualization utilities
- `nucleai.data` - Data processing pipelines

## Development

```bash
# Install dev dependencies
uv sync --dev

# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=nucleai --cov-report=term-missing

# Lint and format
uv run ruff check --fix .
uv run ruff format .

# Check docstring coverage
uv run interrogate -v nucleai
```

## License

TBD
