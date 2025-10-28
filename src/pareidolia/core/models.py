"""Data models for pareidolia."""

from dataclasses import dataclass
from pathlib import Path

from pareidolia.utils.validation import validate_identifier


@dataclass(frozen=True)
class Persona:
    """Represents a persona definition.

    Attributes:
        name: The persona identifier
        content: The persona description and characteristics
    """

    name: str
    content: str

    def __post_init__(self) -> None:
        """Validate persona after initialization."""
        validate_identifier(self.name, "Persona name")
        if not self.content.strip():
            raise ValueError("Persona content cannot be empty")


@dataclass(frozen=True)
class Action:
    """Represents an action template.

    Attributes:
        name: The action identifier
        template: The Jinja2 template content
        persona_name: The name of the associated persona
    """

    name: str
    template: str
    persona_name: str

    def __post_init__(self) -> None:
        """Validate action after initialization."""
        validate_identifier(self.name, "Action name")
        validate_identifier(self.persona_name, "Persona name")
        if not self.template.strip():
            raise ValueError("Action template cannot be empty")


@dataclass(frozen=True)
class Example:
    """Represents an example output.

    Attributes:
        name: The example identifier
        content: The example content (may be a template)
        is_template: Whether the content is a Jinja2 template
    """

    name: str
    content: str
    is_template: bool = False

    def __post_init__(self) -> None:
        """Validate example after initialization."""
        validate_identifier(self.name, "Example name")
        if not self.content.strip():
            raise ValueError("Example content cannot be empty")


@dataclass(frozen=True)
class ExportConfig:
    """Configuration for exporting prompts.

    Attributes:
        tool: The target tool (e.g., 'copilot', 'claude-code')
        library: Optional library name for bundled exports
        output_dir: Directory where prompts will be written
    """

    tool: str
    library: str | None
    output_dir: Path

    def __post_init__(self) -> None:
        """Validate export configuration after initialization."""
        if not self.tool.strip():
            raise ValueError("Tool cannot be empty")
        if self.library is not None:
            validate_identifier(self.library, "Library name")


@dataclass(frozen=True)
class VariantConfig:
    """Configuration for prompt variants.

    Attributes:
        persona: Persona to use as base
        action: Action/task to use as base
        generate: List of variant names to generate
        cli_tool: Optional specific CLI tool to use
    """

    persona: str
    action: str
    generate: list[str]
    cli_tool: str | None = None

    def __post_init__(self) -> None:
        """Validate variant configuration."""
        validate_identifier(self.persona, "Variant persona")
        validate_identifier(self.action, "Variant action")
        if not self.generate:
            raise ValueError("Variant generate list cannot be empty")
        for variant_name in self.generate:
            validate_identifier(variant_name, "Variant name")
        if self.cli_tool is not None and not self.cli_tool.strip():
            raise ValueError("CLI tool name cannot be empty string")
