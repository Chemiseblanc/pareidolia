"""Project initialization logic for pareidolia."""

from pathlib import Path

from pareidolia.core.exceptions import ConfigurationError
from pareidolia.utils.filesystem import ensure_directory, write_file


class ProjectInitializer:
    """Handles initialization of a new Pareidolia project.

    This class provides methods to create configuration files, scaffold
    directory structures, and populate example files for a new Pareidolia
    project.
    """

    # Default configuration template with explanatory comments
    CONFIG_TEMPLATE = """\
# Pareidolia Configuration File
# This file defines the structure and output settings for your prompt library.

[pareidolia]
# Root directory containing your personas, actions, examples, and templates
root = "pareidolia"

[export]
# Target tool for prompt export (e.g., "standard", "copilot", "claude-code")
tool = "standard"

# Optional: Library name for bundled exports
# library = "my-prompts"

# Directory where generated prompts will be written
output_dir = "prompts"

# Optional: Variant generation configuration
# Uncomment and configure to enable automated prompt variants
# [variants]
# persona = "researcher"
# action = "analyze"
# generate = ["expand", "refine", "summarize"]
# cli_tool = "claude"  # Optional: specific CLI tool to use
"""

    # Example persona content
    EXAMPLE_PERSONA = """\
# Researcher Persona

You are an expert research analyst with deep expertise in synthesizing information
from multiple sources and identifying key insights.

## Core Competencies
- Critical analysis of complex information
- Pattern recognition across diverse data sets
- Clear communication of technical concepts
- Evidence-based reasoning

## Approach
- Always cite sources when making claims
- Consider multiple perspectives before drawing conclusions
- Acknowledge limitations and uncertainties
- Focus on actionable insights
"""

    # Example action template content
    EXAMPLE_ACTION = """\
# Analysis Task

You are acting as {{ persona.name }}.

## Objective
Analyze the following {{ subject_type | default("topic") }} and provide a comprehensive
assessment.

## Context
{{ context | default("No additional context provided.") }}

## Requirements
- Identify key themes and patterns
- Highlight important insights
- Note any gaps or limitations in the available information
- Provide actionable recommendations

## Subject to Analyze
{{ subject }}

## Example Output Format
{% if example %}
Here's an example of the expected output format:

{{ example }}
{% endif %}

Please provide your analysis below.
"""

    # Example output content
    EXAMPLE_OUTPUT = """\
# Example Analysis Output

## Executive Summary
This section provides a high-level overview of the key findings.

## Key Findings
1. **Finding One**: Description and supporting evidence
2. **Finding Two**: Description and supporting evidence
3. **Finding Three**: Description and supporting evidence

## Detailed Analysis
### Theme 1: [Theme Name]
Detailed discussion of this theme with supporting evidence and examples.

### Theme 2: [Theme Name]
Detailed discussion of this theme with supporting evidence and examples.

## Recommendations
- Recommendation 1: Specific actionable item
- Recommendation 2: Specific actionable item
- Recommendation 3: Specific actionable item

## Limitations
Discussion of any limitations in the analysis or areas requiring further investigation.
"""

    # Templates directory README
    TEMPLATES_README = """\
# Custom Templates

This directory is for custom Jinja2 templates that you want to use across
multiple actions.

## Usage

You can reference templates in this directory from your action files using
Jinja2's `{% include %}` directive:

```jinja2
{% include "header.md.j2" %}
```

## Example Template

A simple reusable header template (`header.md.j2`):

```jinja2
# {{ title }}
**Date**: {{ date }}
**Author**: {{ persona.name }}

---
```

Then use it in your actions:

```jinja2
{% set title = "Analysis Report" %}
{% set date = "2024-01-15" %}
{% include "header.md.j2" %}

Your action content here...
```

## Best Practices

- Use `.j2` or `.jinja2` extensions for template files
- Keep templates focused and reusable
- Document template variables in comments
- Consider organizing complex templates in subdirectories
"""

    # Gitignore content for output directory
    GITIGNORE_CONTENT = """\
# Ignore all generated prompt files
*

# But keep the .gitignore itself
!.gitignore
"""

    def create_config_file(self, path: Path, overwrite: bool = False) -> None:
        """Create a .pareidolia.toml configuration file.

        Args:
            path: Path where the configuration file should be created
            overwrite: If True, overwrite existing file; if False, raise error
                      if file exists

        Raises:
            ConfigurationError: If file exists and overwrite is False
            IOError: If file cannot be written due to permissions or other
                    filesystem errors
        """
        config_path = path / ".pareidolia.toml"

        if config_path.exists() and not overwrite:
            raise ConfigurationError(
                f"Configuration file already exists: {config_path}\n"
                "Use overwrite=True to replace it."
            )

        try:
            write_file(config_path, self.CONFIG_TEMPLATE)
        except PermissionError as e:
            raise ConfigurationError(
                f"Permission denied: Cannot write configuration file to {config_path}"
            ) from e
        except OSError as e:
            raise ConfigurationError(
                f"Failed to write configuration file to {config_path}: {e}"
            ) from e

    def scaffold_directories(self, root: Path) -> None:
        """Create the directory structure for a Pareidolia project.

        Creates the following directories:
        - personas/ - For persona definition files
        - actions/ - For action template files
        - examples/ - For example output files
        - templates/ - For reusable Jinja2 templates

        Also creates the output directory (prompts/) at the project root level.

        Args:
            root: Root path of the Pareidolia project structure
                 (parent directory should be the project root)

        Raises:
            ConfigurationError: If directories cannot be created due to
                               permissions or other filesystem errors
        """
        # Core directories under the pareidolia root
        directories = [
            root / "personas",
            root / "actions",
            root / "examples",
            root / "templates",
        ]

        # Output directory at project root level
        project_root = root.parent
        directories.append(project_root / "prompts")

        for directory in directories:
            try:
                ensure_directory(directory)
            except PermissionError as e:
                raise ConfigurationError(
                    f"Permission denied: Cannot create directory {directory}"
                ) from e
            except OSError as e:
                raise ConfigurationError(
                    f"Failed to create directory {directory}: {e}"
                ) from e

    def create_example_files(self, root: Path) -> None:
        """Create example/placeholder files in the project structure.

        Creates the following example files:
        - personas/researcher.md - Example persona definition
        - actions/analyze.md.j2 - Example action template
        - examples/analysis-output.md - Example output file
        - templates/README.md - Documentation for custom templates

        Args:
            root: Root path of the Pareidolia project structure

        Raises:
            ConfigurationError: If example files cannot be created due to
                               permissions or other filesystem errors
        """
        example_files = {
            root / "personas" / "researcher.md": self.EXAMPLE_PERSONA,
            root / "actions" / "analyze.md.j2": self.EXAMPLE_ACTION,
            root / "examples" / "analysis-output.md": self.EXAMPLE_OUTPUT,
            root / "templates" / "README.md": self.TEMPLATES_README,
        }

        for file_path, content in example_files.items():
            try:
                write_file(file_path, content)
            except PermissionError as e:
                raise ConfigurationError(
                    f"Permission denied: Cannot write example file to {file_path}"
                ) from e
            except OSError as e:
                raise ConfigurationError(
                    f"Failed to write example file to {file_path}: {e}"
                ) from e

    def create_gitignore(self, path: Path) -> None:
        """Create a .gitignore file in the output directory.

        This prevents generated prompt files from being committed to version
        control while keeping the directory structure.

        Args:
            path: Path to the output directory (typically prompts/)

        Raises:
            ConfigurationError: If .gitignore cannot be created due to
                               permissions or other filesystem errors
        """
        gitignore_path = path / ".gitignore"

        try:
            write_file(gitignore_path, self.GITIGNORE_CONTENT)
        except PermissionError as e:
            raise ConfigurationError(
                f"Permission denied: Cannot write .gitignore file to {gitignore_path}"
            ) from e
        except OSError as e:
            raise ConfigurationError(
                f"Failed to write .gitignore file to {gitignore_path}: {e}"
            ) from e
