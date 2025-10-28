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
- **AI-Powered Variant Generation**: Automatically generate prompt variants (update, refine, summarize, expand) using AI CLI tools

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

## Quick Start

### Initialize a New Project

The fastest way to get started with Pareidolia is using the `init` command:

```bash
# Initialize in the current directory
pareidolia init

# Initialize in a specific directory
pareidolia init my-prompts

# Create only the config file (no example files)
pareidolia init --no-scaffold
```

This creates:
- `.pareidolia.toml` - Configuration file with documented defaults
- `pareidolia/` - Root directory for your prompts
  - `personas/` - Persona definition files
  - `actions/` - Action template files (Jinja2)
  - `examples/` - Example output files
  - `templates/` - Reusable custom templates
- `prompts/` - Output directory for generated prompts

The `init` command also creates example files to demonstrate the structure:
- `pareidolia/personas/researcher.md` - Example persona
- `pareidolia/actions/analyze.md.j2` - Example action template
- `pareidolia/examples/analysis-output.md` - Example output format
- `pareidolia/templates/README.md` - Template usage guide

After initialization, you can immediately try generating prompts:

```bash
pareidolia generate
```

This will create prompts in the `prompts/` directory using the example files.

### Manual Setup

If you prefer to set up your project manually, create the following structure:

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
    ├── example/              # Example outputs (optional Jinja2)
    │   ├── report-format.md
    │   └── output-style.md.j2
    └── variant/              # Variant transformation templates (optional)
        ├── update.md.j2
        ├── refine.md.j2
        ├── summarize.md.j2
        └── expand.md.j2
```

### Configuration (`pareidolia.toml`)

```toml
[pareidolia]
root = "pareidolia"  # Directory containing persona/action/example folders

[generate]
# Default generation settings (can be overridden via CLI)
tool = "copilot"             # or "claude-code", etc.
library = "promptlib"        # Optional: enables library format when set
output_dir = "prompts"       # Where to write generated prompts

[prompts]
# Optional: AI-powered variant generation
persona = "researcher"       # Persona to use as base
action = "research"          # Action to use as base
variants = ["update", "refine", "summarize"]  # List of variants to generate
cli_tool = "claude"          # Optional: specific AI tool (auto-detects if omitted)
```

## Usage

### Getting Started

The recommended way to start a new project is with the `init` command:

```bash
pareidolia init
```

See the [Quick Start](#quick-start) section above for more details.

### Manually Setting Up a Project

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

### Generating Prompts

Generate prompts using the configured settings:

```bash
# Use settings from pareidolia.toml
pareidolia generate

# Override settings via command line
pareidolia generate --tool copilot --output-dir output/

# Generate as a library with tool-specific naming
pareidolia generate --tool copilot --library promptlib
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

## Variant Generation

Pareidolia can automatically generate prompt variants using AI CLI tools. Variants are transformations of base prompts (e.g., "update-research", "refine-research") that are generated during the export process using AI to transform the base prompt according to your variant templates.

The `[prompts]` configuration section controls which variants are generated. The field `variants` contains a list of variant names (like "update", "refine"), while the term "variant" still refers to individual transformation types.

### What Are Variants?

Variants are specialized versions of a base prompt that focus on different tasks:
- **update**: Refreshing or updating existing content
- **refine**: Improving quality and polish of existing content
- **summarize**: Condensing content to essential points
- **expand**: Elaborating with greater depth and detail

### Configuration

Add a `[prompts]` section to your `pareidolia.toml`:

```toml
[prompts]
persona = "researcher"       # Persona to use as base
action = "research"          # Action to use as base  
variants = ["update", "refine", "summarize"]  # Variants to generate
cli_tool = "claude"          # Optional: specific AI tool (auto-detects if omitted)
```

When you run `pareidolia generate`, variants are automatically generated alongside the base prompt if the generated action matches the configured action.

### Variant Templates

Variant templates define how the AI should transform the base prompt. Create them in your `variant/` directory:

```
pareidolia/
└── variant/
    ├── update.md.j2
    ├── refine.md.j2
    ├── summarize.md.j2
    └── expand.md.j2
```

**Template Format:**

Variant templates are Jinja2 templates that receive three variables:
- `{{ persona_name }}` - The persona name (e.g., "researcher")
- `{{ action_name }}` - The action name (e.g., "research")
- `{{ variant_name }}` - The variant being generated (e.g., "update")

**Example variant template (`variant/update.md.j2`):**

```markdown
You are transforming an existing prompt into an "update" variant.

The update variant should modify the original prompt to focus on updating
or refreshing existing content rather than creating new content from scratch.

**Context:**
- Persona: {{ persona_name }}
- Action: {{ action_name }}
- Variant: {{ variant_name }}

**Transformation Instructions:**

1. Keep the core purpose and tone of the original prompt
2. Shift the focus to updating/refreshing existing material
3. Add instructions for handling existing content
4. Maintain the persona's voice and characteristics

Transform the following prompt into an update variant:
```

The AI tool receives both the rendered variant template (with transformation instructions) and the base prompt, then generates the variant accordingly.

**Default Templates:**

Pareidolia includes example templates in `src/pareidolia/templates/defaults/variant/`:
- `update.md.j2` - Instructions for update variants
- `refine.md.j2` - Instructions for refine variants
- `summarize.md.j2` - Instructions for summarize variants
- `expand.md.j2` - Instructions for expand variants

You can copy these to your project's `variant/` directory as starting points.

### Supported CLI Tools

Variant generation requires at least one AI CLI tool:

| Tool | Command | Installation |
|------|---------|--------------|
| **Codex** | `codex` | Install OpenAI Codex CLI |
| **Copilot** | `gh copilot` | Install GitHub CLI and Copilot extension |
| **Claude** | `claude` | Install Anthropic Claude CLI |
| **Gemini** | `gemini` | Install Google Gemini CLI |

**Auto-detection:** If you don't specify `cli_tool` in your config, Pareidolia will automatically use the first available tool from the list above.

**Tool-specific:** To use a specific tool, set it in your config:
```toml
[prompts]
cli_tool = "claude"  # Use Claude for variant generation
```

### Generated Files and Naming

Variants follow a **verb-noun** naming convention:

**Without library:**
```
prompts/
├── research.prompt.md           # Base prompt
├── update-research.prompt.md    # Update variant
├── refine-research.prompt.md    # Refine variant
└── summarize-research.prompt.md # Summarize variant
```

**With library (Claude Code style):**
```
prompts/
└── promptlib/
    ├── research.md
    ├── update-research.md
    ├── refine-research.md
    └── summarize-research.md
```

**With library (GitHub Copilot style):**
```
prompts/
├── promptlib.research.prompt.md
├── promptlib.update-research.prompt.md
├── promptlib.refine-research.prompt.md
└── promptlib.summarize-research.prompt.md
```

### Usage Example

1. **Create variant templates:**
```bash
mkdir -p pareidolia/variant
cp src/pareidolia/templates/defaults/variant/*.md.j2 pareidolia/variant/
```

2. **Configure variants in `pareidolia.toml`:**
```toml
[prompts]
persona = "researcher"
action = "research"
variants = ["update", "refine", "summarize", "expand"]
```

3. **Generate with variants:**
```bash
pareidolia generate
```

This will generate:
- `research.prompt.md` (base prompt)
- `update-research.prompt.md` (AI-generated update variant)
- `refine-research.prompt.md` (AI-generated refine variant)
- `summarize-research.prompt.md` (AI-generated summarize variant)
- `expand-research.prompt.md` (AI-generated expand variant)

### Troubleshooting

**No variants generated:**
- Ensure at least one AI CLI tool is installed and available in your PATH
- Check that the `action` in `[prompts]` matches the action being generated
- Verify variant templates exist in your `variant/` directory

**CLI tool not found:**
- Install the required CLI tool or specify a different one with `cli_tool`
- Check tool installation: `which claude`, `which gh`, etc.

**Template not found:**
- Ensure variant templates exist with supported extensions: `.md.j2`, `.md.jinja`, `.md.jinja2`, or `.md`
- Copy from defaults: `cp src/pareidolia/templates/defaults/variant/*.md.j2 pareidolia/variant/`

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
