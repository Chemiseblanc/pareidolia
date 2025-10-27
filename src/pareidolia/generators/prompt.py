"""Prompt generation functionality."""

from pathlib import Path

from pareidolia.generators.naming import NamingConvention
from pareidolia.templates.composer import PromptComposer
from pareidolia.utils.filesystem import ensure_directory, write_file


class PromptGenerator:
    """Generates individual prompt files.

    Attributes:
        composer: Prompt composer for rendering templates
        naming: Naming convention strategy
    """

    def __init__(
        self,
        composer: PromptComposer,
        naming: NamingConvention,
    ) -> None:
        """Initialize the prompt generator.

        Args:
            composer: Prompt composer
            naming: Naming convention
        """
        self.composer = composer
        self.naming = naming

    def generate(
        self,
        action_name: str,
        persona_name: str,
        output_dir: Path,
        library: str | None = None,
        example_names: list[str] | None = None,
    ) -> Path:
        """Generate a prompt file.

        Args:
            action_name: Name of the action
            persona_name: Name of the persona
            output_dir: Base output directory
            library: Optional library name
            example_names: Optional list of example names

        Returns:
            Path to the generated file

        Raises:
            PersonaNotFoundError: If persona is not found
            ActionNotFoundError: If action is not found
            TemplateRenderError: If rendering fails
            IOError: If file cannot be written
        """
        # Compose the prompt
        prompt = self.composer.compose(action_name, persona_name, example_names)

        # Determine output path
        output_path = self.naming.get_output_path(output_dir, action_name, library)

        # Ensure output directory exists
        ensure_directory(output_path.parent)

        # Write the prompt
        write_file(output_path, prompt)

        return output_path
