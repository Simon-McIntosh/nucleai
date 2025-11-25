# Agent Guidelines

## Introduction

This project, `nucleai`, provides AI-driven support for fusion experiments. It enables the extraction of features from fusion data, generates descriptions and vector embeddings for both feature images and text, and facilitates advanced search capabilities across databases using text and feature shapes. Designed as a codegen-first library, it empowers users to request complex data plotting and processing workflows.

The project also enables natural language data search, retrieval, analysis, and display. It allows users to ask questions about their data and test hypotheses through an intuitive interface.

## Project Setup

### Terminal Usage

**Python execution**: Use `uv run` for all Python commands. This ensures the virtual environment is activated automatically.

```bash
# Run Python scripts
uv run python script.py

# Run modules
uv run python -m nucleai.cli

# Run pytest
uv run pytest

# Run with arguments
uv run python -c "import nucleai; print(nucleai.__version__)"

# Wrong: Don't use system Python or manual activation
python script.py                    # May use wrong Python
source .venv/bin/activate && python # Unnecessary
```

### Package Management
- **Package manager**: `uv`
- **Add dependencies**: `uv add <package>`
- **Add dev dependencies**: `uv add --dev <package>`
- **Sync and lock**: `uv sync`

### CLI Tools
- **Framework**: Use `click` for all CLI tools
- **Progress display**: Use `rich` for progress bars and formatted output
- **Entry points**: Configure in `[project.scripts]` section of `pyproject.toml`

### Code Quality
- **Pre-commit hooks**: Enabled for all commits
- **Linting & formatting**: `ruff` (configuration in `pyproject.toml`)

### Version Control
- **Branch naming**: Use `main` as default branch
- **GitHub CLI**: `gh` is installed in `~/.local/bin` and available in PATH
- **Authentication**: HTTPS protocol (SSH port 22 blocked on this system)
- **Commit messages**: Use conventional commit format with detailed body

**Common gh commands**:
```bash
gh repo create <name> --public --description "..."  # Create repository
gh repo edit --default-branch main                  # Change default branch
gh pr create --title "..." --body "..."             # Create pull request
gh issue create --title "..." --body "..."          # Create issue
gh repo view --web                                  # Open repo in browser
```

**Git workflow**:
```bash
git status                      # Check current state
git add -A                      # Stage all changes
git commit -m "message"         # Commit with message (triggers pre-commit)
git push origin main            # Push to remote
git pull origin main            # Pull latest changes
```

### Testing
- **Framework**: `pytest`
- **Coverage target**: 100%
- **Reusable fixtures**: Define in `conftest.py` files
- **Commit standard**: All tests must pass before committing

**Test philosophy**:
- **Test behavior, not implementation**: Focus on what the code does, not how it does it
- **Test public interfaces**: Avoid testing private methods or internal state
- **Keep tests flexible**: Early-stage tests should allow implementation changes without breaking
- **Use black-box testing**: Test inputs and outputs without depending on internal structure

**Best practices**:
- Prefer integration tests over unit tests where practical
- Mock external dependencies (databases, file system, network) but avoid excessive mocking
- Test edge cases and error conditions
- Use parameterized tests for multiple input scenarios
- Keep test names descriptive: `test_extract_features_raises_error_for_empty_data`

```python
# Good: Tests behavior through public interface
async def test_search_returns_relevant_results():
    results = await search_features("elm_event")
    assert len(results) > 0
    assert results[0].similarity > 0.8

# Avoid: Tests implementation details
async def test_search_calls_embedding_model():
    # Don't test internal model calls
    ...
```

## Project Structure

```
nucleai/
├── core/          # Core data models and base interfaces
├── features/      # Feature extraction from fusion data
├── embeddings/    # Vector embedding generation (text and image)
├── search/        # Semantic and shape-based search
├── plot/          # Visualization and plotting utilities
└── data/          # Data processing pipelines

tests/
├── conftest.py    # Shared test fixtures
└── */             # Mirror source structure
```

**Organization principles**:
- Mirror test structure to source structure
- Group related functionality in focused modules
- Keep modules cohesive and loosely coupled

## Python Style Guide

### Version & Modern Practices
- **Python version**: 3.13 (recommended)
- Follow modern Python standards and relevant PEPs
- No `from __future__ import` statements
- No `from typing import` or `if TYPE_CHECKING` guards

### Import Style
```python
# All imports at top of file, ordered:
# 1. Standard library
# 2. Third-party packages
# 3. Local imports

import os
import sys

import anyio
import pydantic

from nucleai.core import models
```

### Type Annotations
- Type all functions and classes
- Use modern type syntax (e.g., `list[str]` not `List[str]`)

```python
def process_features(items: list[str], threshold: float = 0.5) -> dict[str, int]:
    """Process items and return counts."""
    ...
```

### Data Structures
- **Schemas**: Use `pydantic` models
- **Data classes**: Use `dataclasses` for non-schema classes
- **Avoid**: Bare `class` definitions where dataclasses/pydantic apply

```python
from dataclasses import dataclass

import pydantic


class FeatureSchema(pydantic.BaseModel):
    """Feature data schema."""
    name: str
    description: str
    embedding: list[float]


@dataclass
class Config:
    """Application configuration."""
    timeout: float
    retries: int
```

### Asynchronous Programming
- **Library**: Use `anyio` for async operations
- **When to use async**: All separable I/O-bound processes
  - Data retrieval
  - Network requests
  - File I/O operations
  - Database queries
  - Embedding generation (if remote)

```python
import anyio


async def load_data(file_path: str) -> Data:
    """Load data asynchronously."""
    async with anyio.open_file(file_path) as f:
        content = await f.read()
    return Data.parse(content)
```

### Design Patterns
- **Prefer**: Composition over inheritance
- **Use inheritance**: Only when it provides clear benefits
- Favor explicit over implicit

### Error Handling

**Best practices**:
- Use specific exception types, not bare `except:`
- Let exceptions propagate unless you can handle them meaningfully
- Validate inputs early with clear error messages
- Use context managers for resource cleanup

```python
async def generate_embedding(text: str) -> list[float]:
    """Generate vector embedding for text.
    
    Raises:
        ValueError: If text is empty
        ModelError: If embedding model fails
    """
    if not text.strip():
        raise ValueError("text cannot be empty")
    
    try:
        return await model_client.embed(text)
    except APIError as e:
        raise ModelError(f"Failed to generate embedding: {e}") from e
```

**Exception guidelines**:
- Raise built-in exceptions when appropriate (`ValueError`, `TypeError`, etc.)
- Create custom exceptions for domain-specific errors
- Include context in exception messages
- Use exception chaining with `from` to preserve stack traces

## Documentation

### Public Methods
- Include concise docstrings for all public methods and classes
- Add usage examples in markdown format where helpful
- Document exceptions that may be raised

```python
def extract_features(data: FusionData, config: Config) -> list[Feature]:
    """Extract features from fusion data based on configuration.
    
    ## Example
    
    ```python
    features = extract_features(data, config)
    print(len(features))
    ```
    
    Raises:
        ValueError: If data is invalid
    """
    ...
```

## Code Philosophy

### Green Field Project
- No backward compatibility constraints
- Avoid terms like "new", "refactored", "enhanced", "replaces" in:
  - Comments
  - Module names
  - Class names
  - Function names

Write code as if it's always been this way.
