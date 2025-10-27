# Pareidolia

A command-line tool for generating collections of AI prompt templates for persona-based agents.

## Overview

Pareidolia enables you to create modular, reusable AI prompt templates by separating concerns into:
- **Personas**: Define the agent's role and characteristics (`.md` files)
- **Actions**: Specify tasks the agent should perform (`.md.j2`, `.md.jinja`, or `.md.jinja2` templates)
- **Examples**: Provide output formatting examples (`.md` or templated files)

These components are compiled into complete prompt files using Jinja2 templating, making it easy to maintain consistent agent behaviors across multiple tools.

## Features

- **Modular Prompt Design**: Separate persona, action, and example definitions
- **Jinja2 Templating**: Powerful templating engine for flexible prompt composition
- **Multi-Tool Support**: Export prompts with naming conventions for different AI tools (Claude Code, GitHub Copilot, etc.)
- **Library Bundling**: Bundle related prompts into reusable libraries with consistent prefixes
- **Configurable Exports**: Define default export settings in `pareidolia.toml` with CLI overrides

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd pareidolia

# Install with uv
uv sync

# Run the CLI
uv run pareidolia --help
```

## Project Structure

A Pareidolia project consists of:

```
your-project/
├── pareidolia.toml           # Configuration file
└── pareidolia/               # Default root (configurable)
    ├── persona/              # Persona definitions
    │   └── researcher.md
    ├── action/               # Action templates (Jinja2)
    │   ├── research.md.j2
    │   ├── refine-research.md.jinja
    │   └── update-research.md.jinja2
    └── example/              # Example outputs (optional Jinja2)
        ├── report-format.md
        └── output-style.md.j2
```

### Configuration (`pareidolia.toml`)

```toml
[pareidolia]
root = "pareidolia"  # Directory containing persona/action/example folders

[export]
# Default export settings (can be overridden via CLI)
tool = "copilot"             # or "claude-code", etc.
library = "promptlib"        # Optional: enables library format when set
output_dir = "prompts"       # Where to write generated prompts
```

## Usage

### Setting Up a Project

1. Create the project structure:
```bash
mkdir -p pareidolia/{persona,action,example}
```

2. Create personas in `pareidolia/persona/`:
```markdown
<!-- pareidolia/persona/researcher.md -->
You are an expert researcher with deep analytical skills...
```

3. Create action templates in `pareidolia/action/`:
```markdown
<!-- pareidolia/action/research.md.j2 -->
{{ persona }}

Your task is to research the following topic...
```

4. Add example outputs in `pareidolia/example/` (optional):
```markdown
<!-- pareidolia/example/report-format.md -->
# Research Report Example
...
```

### Exporting Prompts

Export prompts using the configured settings:

```bash
# Use settings from pareidolia.toml
pareidolia export

# Override settings via command line
pareidolia export --tool copilot --output-dir output/

# Export as a library with tool-specific naming
pareidolia export --tool copilot --library promptlib
```

### Output Examples

**Standard format (no --library option):**
```
output/
├── research.prompt.md
├── refine-research.prompt.md
└── update-research.prompt.md
```

**Library format with Claude Code (--tool claude-code --library promptlib):**
```
output/
└── promptlib/
    ├── research.md
    ├── refine-research.md
    └── update-research.md
```

**Library format with GitHub Copilot (--tool copilot --library promptlib):**
```
output/
├── promptlib.research.prompt.md
├── promptlib.refine-research.prompt.md
└── promptlib.update-research.prompt.md
```

## Project Structure

```
pareidolia/
├── src/
│   └── pareidolia/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli.py           # Command-line interface
│       ├── core/            # Core functionality (config, models)
│       ├── templates/       # Template management and rendering
│       └── generators/      # Prompt generators and exporters
├── tests/                   # Test suite (pytest)
├── examples/                # Example projects
├── pyproject.toml
├── README.md
└── AGENTS.md
```

## Development

### Setup

```bash
# Install development dependencies
uv sync --dev

# Run tests
uv run pytest

# Run linting
uv run ruff check .
uv run mypy src/
```

### Workflow

- Feature branching is used for all development
- Changes are broken into logical commits following Linux kernel commit message guidelines
- All code uses type hints and passes linting
- Complete test coverage with pytest

### Commit Message Format

```
component: short description (50 chars or less)

More detailed explanatory text, if necessary. Wrap at 72 characters.
Explain the problem that this commit is solving. Focus on why you are
making this change as opposed to how.

- Bullet points are okay
- Use a dash or asterisk for bullets
```

## Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=pareidolia --cov-report=html

# Run specific test file
uv run pytest tests/test_cli.py
```

## Contributing

1. Create a feature branch from `master`
2. Make your changes with proper type hints and linting
3. Add tests for new functionality
4. Ensure all tests pass
5. Commit with descriptive messages
6. Merge back to `master` when complete

## License

[Add your license here]

## Authors

[Add authors here]
