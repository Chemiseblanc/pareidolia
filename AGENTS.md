# Agent Guidelines for Pareidolia Development

This document outlines the development guidelines and best practices for AI agents working on the Pareidolia project.

## Project Overview

Pareidolia is a Python CLI application for generating AI prompt template collections. It uses modular components (personas, tasks, examples) compiled via Jinja2 templates into complete prompt files.

## Working Memory

**All planning, requirements, design, and other working documents must be stored in the `.working-memory/` folder unless explicitly instructed otherwise.** This keeps project artifacts organized and separate from source code and user-facing documentation.

## Core Principles

### 1. Code Quality

- **Type Hints**: All functions, methods, and variables must use proper type hints
- **Linting**: Code must pass ruff and mypy checks before committing
- **Documentation**: Docstrings required for all public APIs (Google style)
- **Testing**: pytest test coverage for all new features

### 2. Architecture Guidelines

#### Module Organization

```
src/pareidolia/
├── __init__.py
├── __main__.py
├── cli.py                 # CLI entry point, argument parsing
├── core/
│   ├── __init__.py
│   ├── persona.py        # Persona data models and logic
│   ├── task.py           # Task data models and logic
│   ├── example.py        # Example data models and logic
│   └── library.py        # Library bundling logic
├── templates/
│   ├── __init__.py
│   ├── engine.py         # Jinja2 template engine
│   ├── loader.py         # Template loading and caching
│   └── defaults/         # Default template files
├── generators/
│   ├── __init__.py
│   ├── prompt.py         # Prompt generation
│   └── naming.py         # Tool-specific naming conventions
└── utils/
    ├── __init__.py
    ├── filesystem.py     # File I/O utilities
    └── validation.py     # Input validation
```

### 3. Design Patterns

- **Separation of Concerns**: Keep CLI, business logic, and I/O separate
- **Dependency Injection**: Pass dependencies rather than importing globals
- **Immutability**: Use dataclasses with frozen=True where appropriate
- **Type Safety**: Leverage mypy strict mode for maximum type checking

#### Example Type Hints

```python
from typing import Protocol, TypedDict
from pathlib import Path
from dataclasses import dataclass

class TemplateEngine(Protocol):
    def render(self, template: str, context: dict[str, Any]) -> str: ...

@dataclass(frozen=True)
class Persona:
    name: str
    description: str
    characteristics: list[str]
    
@dataclass(frozen=True)
class Task:
    name: str
    persona: str
    instructions: str
    output_format: str | None = None

def generate_prompt(
    persona: Persona,
    task: Task,
    examples: list[str],
    template_engine: TemplateEngine,
) -> str:
    """Generate a complete prompt from components.
    
    Args:
        persona: The persona definition
        task: The task definition
        examples: List of example outputs
        template_engine: Template rendering engine
        
    Returns:
        Rendered prompt content
        
    Raises:
        ValueError: If required fields are missing
    """
    ...
```

## Testing Requirements

### Test Structure

```
tests/
├── conftest.py              # Shared fixtures
├── unit/
│   ├── test_persona.py
│   ├── test_task.py
│   ├── test_template_engine.py
│   └── test_generators.py
├── integration/
│   ├── test_cli.py
│   └── test_end_to_end.py
└── fixtures/
    ├── personas/
    ├── tasks/
    └── templates/
```

### Testing Guidelines

- **Unit tests**: Test individual functions and classes in isolation
- **Integration tests**: Test CLI commands and workflows
- **Fixtures**: Use pytest fixtures for common test data
- **Parametrize**: Use `pytest.mark.parametrize` for multiple test cases
- **Coverage**: Aim for >90% code coverage
- **Test naming**: Use descriptive names: `test_<what>_<condition>_<expected>`

### Example Tests

```python
import pytest
from pareidolia.core.persona import Persona

def test_persona_creation_with_valid_data():
    persona = Persona(
        name="researcher",
        description="An expert researcher",
        characteristics=["thorough", "analytical"]
    )
    assert persona.name == "researcher"

@pytest.mark.parametrize("invalid_name", ["", " ", "invalid name", "123"])
def test_persona_creation_rejects_invalid_names(invalid_name: str):
    with pytest.raises(ValueError, match="Invalid persona name"):
        Persona(name=invalid_name, description="Test", characteristics=[])
```

## Development Workflow

1. **Start feature**:
   ```bash
   git checkout master
   git pull
   git checkout -b feature/library-creation
   ```

2. **Develop with tests**:
   - Write failing test
   - Implement feature
   - Ensure test passes
   - Run full test suite
   - Run linting

3. **Commit changes**:
   ```bash
   # Stage related changes
   git add src/pareidolia/core/library.py tests/unit/test_library.py
   
   # Commit with proper message
   git commit -m "core: add library bundling functionality

   Implement Library class to bundle multiple prompts with consistent
   naming conventions. Supports tool-specific prefixes for Claude Code
   and GitHub Copilot.
   
   - Add Library dataclass with validation
   - Implement prefix mapping for different tools
   - Add comprehensive unit tests"
   ```

4. **Verify before merge**:
   ```bash
   uv run pytest
   uv run ruff check .
   uv run mypy src/
   ```

5. **Merge to master**:
   ```bash
   git checkout master
   git merge --no-ff feature/library-creation
   git branch -d feature/library-creation
   ```

## Dependencies

- **Runtime**: Jinja2 (templating)
- **Development**: pytest, ruff, mypy, pytest-cov
- **Typing**: Use `typing` module, `typing_extensions` if needed

Add dependencies using uv:
```bash
uv add jinja2
uv add --dev pytest ruff mypy pytest-cov
```

## Common Tasks for AI Agents

When asked to implement features:

1. **Create feature branch** from master
2. **Read existing code** to understand patterns
3. **Add type hints** to all new code
4. **Write tests first** (TDD approach preferred)
5. **Implement feature** with proper error handling
6. **Run test suite** and ensure all tests pass
7. **Run linters** (ruff, mypy) and fix issues
8. **Commit with proper message** following guidelines
9. **Verify merge-readiness** before merging to master

## Error Handling

- Use specific exception types
- Provide helpful error messages
- Validate inputs early
- Use type hints to prevent errors

```python
class PareidoliaError(Exception):
    """Base exception for pareidolia."""

class PersonaNotFoundError(PareidoliaError):
    """Raised when a persona cannot be found."""

class InvalidTemplateError(PareidoliaError):
    """Raised when a template is invalid."""

def load_persona(name: str) -> Persona:
    """Load a persona by name.
    
    Args:
        name: Persona name to load
        
    Returns:
        Loaded persona
        
    Raises:
        PersonaNotFoundError: If persona does not exist
        ValueError: If name is empty or invalid
    """
    if not name or not name.strip():
        raise ValueError("Persona name cannot be empty")
    # ... implementation
```

## Summary

- Write clean, typed, tested Python code
- Follow Linux kernel commit message format
- Use feature branches and logical commits
- Maintain high test coverage
- Run linters before committing
- Focus on modularity and separation of concerns

This ensures the Pareidolia codebase remains maintainable, well-tested, and easy to understand.
