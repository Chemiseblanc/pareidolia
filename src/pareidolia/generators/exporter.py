"""Export functionality for generating multiple prompts."""

from dataclasses import dataclass
from pathlib import Path

from pareidolia.core.config import PareidoliaConfig
from pareidolia.generators.naming import get_naming_convention
from pareidolia.generators.prompt import PromptGenerator
from pareidolia.templates.composer import PromptComposer
from pareidolia.templates.engine import Jinja2Engine
from pareidolia.templates.loader import TemplateLoader


@dataclass
class ExportResult:
    """Result of an export operation.

    Attributes:
        success: Whether the export was successful
        files_generated: List of generated file paths
        errors: List of error messages
    """

    success: bool
    files_generated: list[Path]
    errors: list[str]


class Exporter:
    """Exports prompts for all actions in a project.

    Attributes:
        config: Pareidolia configuration
        loader: Template loader
        composer: Prompt composer
        generator: Prompt generator
    """

    def __init__(self, config: PareidoliaConfig) -> None:
        """Initialize the exporter.

        Args:
            config: Pareidolia configuration
        """
        self.config = config
        self.loader = TemplateLoader(config.root)
        self.composer = PromptComposer(self.loader, Jinja2Engine())

        naming = get_naming_convention(config.export.tool)
        self.generator = PromptGenerator(self.composer, naming)

    def export_all(
        self,
        persona_name: str | None = None,
        example_names: list[str] | None = None,
    ) -> ExportResult:
        """Export all actions to prompt files.

        Args:
            persona_name: Optional persona name (uses first available if not specified)
            example_names: Optional list of example names to include

        Returns:
            Export result with list of generated files and any errors
        """
        files_generated: list[Path] = []
        errors: list[str] = []

        # Get list of all actions
        actions = self.loader.list_actions()

        if not actions:
            errors.append("No actions found in project")
            return ExportResult(
                success=False,
                files_generated=files_generated,
                errors=errors,
            )

        # Determine persona to use
        if persona_name is None:
            personas = self.loader.list_personas()
            if not personas:
                errors.append("No personas found in project")
                return ExportResult(
                    success=False,
                    files_generated=files_generated,
                    errors=errors,
                )
            persona_name = personas[0]

        # Get output directory from config (already a Path)
        output_dir = self.config.export.output_dir

        # Generate prompts for each action
        for action_name in actions:
            try:
                output_path = self.generator.generate(
                    action_name=action_name,
                    persona_name=persona_name,
                    output_dir=output_dir,
                    library=self.config.export.library,
                    example_names=example_names,
                )
                files_generated.append(output_path)
            except Exception as e:
                errors.append(f"Failed to generate {action_name}: {e}")

        success = len(errors) == 0
        return ExportResult(
            success=success,
            files_generated=files_generated,
            errors=errors,
        )

    def export_action(
        self,
        action_name: str,
        persona_name: str,
        example_names: list[str] | None = None,
    ) -> ExportResult:
        """Export a single action to a prompt file.

        Args:
            action_name: Name of the action to export
            persona_name: Name of the persona to use
            example_names: Optional list of example names to include

        Returns:
            Export result with generated file path and any errors
        """
        files_generated: list[Path] = []
        errors: list[str] = []

        # Get output directory from config (already a Path)
        output_dir = self.config.export.output_dir

        try:
            output_path = self.generator.generate(
                action_name=action_name,
                persona_name=persona_name,
                output_dir=output_dir,
                library=self.config.export.library,
                example_names=example_names,
            )
            files_generated.append(output_path)
        except Exception as e:
            errors.append(f"Failed to generate {action_name}: {e}")

        success = len(errors) == 0
        return ExportResult(
            success=success,
            files_generated=files_generated,
            errors=errors,
        )
