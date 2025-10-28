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

### 1. Initialize a New Project

```bash
# Initialize in the current directory
pareidolia init

# Initialize in a specific directory
pareidolia init my-prompts

# Create only the config file (no example files)
pareidolia init --no-scaffold
```

### 2. Generate Prompts

```bash
# Use settings from pareidolia.toml
pareidolia generate

# Override settings via command line
pareidolia generate --tool copilot --output-dir output/

# Generate as a library with tool-specific naming
pareidolia generate --tool copilot --library promptlib
```

## Project Structure

The `init` command creates this structure:

```
your-project/
├── pareidolia.toml           # Configuration file
├── pareidolia/               # Default root (configurable)
│   ├── personas/             # Persona definitions
│   │   └── researcher.md
│   ├── actions/              # Action templates (Jinja2)
│   │   └── analyze.md.j2
│   ├── examples/             # Example outputs (optional Jinja2)
│   │   └── analysis-output.md
│   └── templates/            # Custom templates (optional)
└── prompts/                  # Generated output directory
```

Optional directories for advanced features:
```
pareidolia/
└── variant/                  # AI-powered variant templates
    ├── update.md.j2
    ├── refine.md.j2
## Configuration

Create a `pareidolia.toml` file (automatically created by `init`):

```toml
[pareidolia]
root = "pareidolia"  # Directory containing persona/action/example folders

[generate]
tool = "copilot"             # or "claude-code", etc.
library = "promptlib"        # Optional: enables library format when set
output_dir = "prompts"       # Where to write generated prompts

# Global metadata - applies to all prompts by default
[metadata]
model = "claude-3.5-sonnet"
temperature = 0.7
tags = ["analysis", "research"]

[prompts]
# Optional: AI-powered variant generation (see Variant Generation section)
persona = "researcher"
action = "research"
variants = ["update", "refine", "summarize"]
cli_tool = "claude"          # Optional: auto-detects if omitted

# Per-prompt metadata - overrides global metadata
[prompts.metadata]
mode = "agent"
description = "Conducts and reports research findings"
# Inherits model, temperature, and tags from global [metadata]
```

## Output Formats

**Standard format:**
```
prompts/
├── research.prompt.md
├── refine-research.prompt.md
└── update-research.prompt.md
```

**Library format (Claude Code):**
```
prompts/promptlib/
├── research.md
├── refine-research.md
└── update-research.md
```

**Library format (GitHub Copilot):**
```
prompts/
├── promptlib.research.prompt.md
├── promptlib.refine-research.prompt.md
└── promptlib.update-research.prompt.md
```put/
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
## Tool-Specific Metadata and Frontmatter

Pareidolia supports attaching metadata to prompts for generating tool-specific frontmatter. Metadata can be defined globally (applying to all prompts) or per-prompt (overriding global settings).

### Configuration

#### Global Metadata

Define default metadata for all prompts in the `[metadata]` section:

```toml
[metadata]
model = "claude-3.5-sonnet"
temperature = 0.7
max_tokens = 4096
tags = ["default", "analysis"]
```

#### Per-Prompt Metadata

Override or extend global metadata for specific prompts using `[prompts.metadata]`:

```toml
[prompts]
persona = "researcher"
action = "analyze"
variants = ["expand", "refine"]

[prompts.metadata]
mode = "agent"
model = "Claude Sonnet 4"  # Overrides global model
description = "Research analysis assistant"
# Inherits temperature, max_tokens, and tags from global [metadata]
```

#### Merging Behavior

- Global metadata applies to all prompts by default
- Per-prompt metadata overrides global values for the same keys
- Values not specified in per-prompt metadata are inherited from global metadata
- Both sections are optional and default to empty if omitted

**Example:**

```toml
# Global defaults
[metadata]
model = "claude-3.5-sonnet"
temperature = 0.7
max_tokens = 4096

# Per-prompt overrides
[prompts.metadata]
mode = "agent"
model = "Claude Sonnet 4"

# Result: prompts will have:
# - model: "Claude Sonnet 4" (overridden)
# - temperature: 0.7 (inherited)
# - max_tokens: 4096 (inherited)
# - mode: "agent" (added)
```

### Accessing Metadata in Templates

Templates can access metadata through the `{{ metadata }}` variable, along with `{{ tool }}` and `{{ library }}`. The metadata available in templates is the merged result of global and per-prompt metadata:

```jinja2
{%- if metadata -%}
---
{%- if metadata.description %}
description: {{ metadata.description }}
{%- endif %}
{%- if metadata.model %}
model: {{ metadata.model }}
{%- endif %}
{%- if metadata.mode %}
mode: {{ metadata.mode }}
{%- endif %}
{%- if tool %}
tool: {{ tool }}
{%- endif %}
---

{% endif -%}
# {{ persona }}

Your template content here...
```

### Tool-Specific Examples

**Global + Per-Prompt Configuration:**

```toml
# Global defaults for all prompts
[metadata]
temperature = 0.7
max_tokens = 4096
tags = ["production", "v1"]

# GitHub Copilot prompt
[prompts]
persona = "reviewer"
action = "review"
variants = ["refine"]

[prompts.metadata]
description = "Code review assistant"
tags = ["code-review", "best-practices"]  # Overrides global tags
# Inherits temperature and max_tokens
```

Generated frontmatter:
```yaml
---
description: Code review assistant
tags: ["code-review", "best-practices"]
temperature: 0.7
max_tokens: 4096
---
```

**Claude Code with Global Defaults:**

```toml
[metadata]
model = "claude-3.5-sonnet"
temperature = 0.7

[prompts.metadata]
description = "Research analysis assistant"
chat_mode = "extended"
# Inherits model and temperature from global
```

Generated frontmatter:
```yaml
---
description: Research analysis assistant
model: claude-3.5-sonnet
chat_mode: extended
temperature: 0.7
---
```

**Using Only Global Metadata:**

```toml
[metadata]
description = "General purpose assistant"
version = "1.0"
author = "Your Name"
model = "claude-3.5-sonnet"

[prompts]
persona = "assistant"
action = "help"
variants = []
# No [prompts.metadata] - uses global metadata only
```

### Common Metadata Fields

The following fields are commonly used across different tools:

| Field | Type | Description | Tools |
|-------|------|-------------|-------|
| `description` | string | Brief description of prompt's purpose | All |
| `model` | string | Preferred AI model (e.g., "claude-3.5-sonnet") | Claude, OpenAI |
| `chat_mode` | string | Chat mode setting (e.g., "extended", "concise") | Claude Code |
| `tags` | list | Categorization tags | Copilot, general |
| `temperature` | number | Sampling temperature (0.0-1.0) | Most LLM tools |
| `max_tokens` | number | Maximum response length | Most LLM tools |
| `version` | string | Prompt version identifier | General |
| `author` | string | Prompt author | General |

You can use any metadata fields that make sense for your use case. The template determines which fields appear in the generated frontmatter.

## Variant Generation

Pareidolia can automatically generate prompt variants using AI CLI tools. Variants are specialized versions of a base prompt:
- **update**: Refreshing or updating existing content
- **refine**: Improving quality and polish
- **summarize**: Condensing to essential points
- **expand**: Elaborating with greater depth

When you run `pareidolia generate`, variants are automatically created alongside the base prompt if the action matches your configuration.
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
### Setting Up Variants

1. **Copy default templates:**
```bash
mkdir -p pareidolia/variant
cp src/pareidolia/templates/defaults/variant/*.md.j2 pareidolia/variant/
```

2. **Configure in `pareidolia.toml`:**
```toml
[prompts]
persona = "researcher"
action = "research"
variants = ["update", "refine", "summarize"]
```

3. **Generate:**
```bash
pareidolia generate
```

### Template Format

Variant templates are Jinja2 templates with three variables:
- `{{ persona_name }}` - The persona name
- `{{ action_name }}` - The action name
- `{{ variant_name }}` - The variant being generated

Example template structure:
```markdown
Transform the following prompt into a "{{ variant_name }}" variant.

Instructions:
1. Keep the core purpose and tone
2. Focus on {{ variant_name }}-specific tasks
3. Maintain the persona's voice

[Transformation instructions here...]
```
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
### Supported CLI Tools

Pareidolia auto-detects the first available AI CLI tool:

| Tool | Command | Installation |
|------|---------|--------------|
| **Codex** | `codex` | Install OpenAI Codex CLI |
| **Copilot** | `gh copilot` | Install GitHub CLI and Copilot extension |
| **Claude** | `claude` | Install Anthropic Claude CLI |
| **Gemini** | `gemini` | Install Google Gemini CLI |

Override auto-detection in your config:
```toml
[prompts]
cli_tool = "claude"
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
### Troubleshooting Variants

- **No variants generated:** Check that `action` in `[prompts]` matches the action being generated and AI CLI tool is installed
- **CLI tool not found:** Install a supported tool or specify one with `cli_tool`
- **Template not found:** Copy defaults: `cp src/pareidolia/templates/defaults/variant/*.md.j2 pareidolia/variant/`