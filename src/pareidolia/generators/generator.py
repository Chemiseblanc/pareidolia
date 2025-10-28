"""Generate functionality for generating multiple prompts."""

import logging
from dataclasses import dataclass
from pathlib import Path

from pareidolia.core.config import PareidoliaConfig
from pareidolia.core.exceptions import ActionNotFoundError
from pareidolia.generators.cli_tools import (
    CLITool,
    get_available_tools,
    get_tool_by_name,
)
from pareidolia.generators.naming import get_naming_convention
from pareidolia.generators.prompt import PromptGenerator
from pareidolia.generators.variants import VariantGenerator
from pareidolia.templates.composer import PromptComposer
from pareidolia.templates.engine import Jinja2Engine
from pareidolia.templates.loader import TemplateLoader

logger = logging.getLogger(__name__)


@dataclass
class GenerateResult:
    """Result of a generate operation.

    Attributes:
        success: Whether the generation was successful
        files_generated: List of generated file paths
        errors: List of error messages
    """

    success: bool
    files_generated: list[Path]
    errors: list[str]


class Generator:
    """Generates prompts for all actions in a project.

    Attributes:
        config: Pareidolia configuration
        loader: Template loader
        composer: Prompt composer
        generator: Prompt generator
    """

    def __init__(self, config: PareidoliaConfig) -> None:
        """Initialize the generator.

        Args:
            config: Pareidolia configuration
        """
        self.config = config
        self.loader = TemplateLoader(config.root)
        self.composer = PromptComposer(
            self.loader, Jinja2Engine(), config.generate
        )

        self.naming = get_naming_convention(config.generate.tool)
        self.generator = PromptGenerator(self.composer, self.naming)
        self.variant_generator = VariantGenerator(
            self.loader, self.composer, config.generate
        )

    def generate_all(
        self,
        persona_name: str | None = None,
        example_names: list[str] | None = None,
    ) -> GenerateResult:
        """Generate all actions to prompt files.

        Args:
            persona_name: Optional persona name (uses first available if not specified)
            example_names: Optional list of example names to include

        Returns:
            Generate result with list of generated files and any errors
        """
        files_generated: list[Path] = []
        errors: list[str] = []

        # Get list of all actions
        actions = self.loader.list_actions()

        if not actions:
            errors.append("No actions found in project")
            return GenerateResult(
                success=False,
                files_generated=files_generated,
                errors=errors,
            )

        # Filter out variant actions to avoid duplicates
        # If an action matches {variant}-{base_action} pattern where:
        # - base_action is configured in prompts.action
        # - variant is in prompts.variants
        # Then skip it as it will be generated as a variant
        filtered_actions = []
        for action_name in actions:
            should_skip = False
            if self.config.prompts:
                for variant_name in self.config.prompts.variants:
                    variant_action = f"{variant_name}-{self.config.prompts.action}"
                    if action_name == variant_action:
                        should_skip = True
                        break
            if not should_skip:
                filtered_actions.append(action_name)

        actions = filtered_actions

        # Determine persona to use
        if persona_name is None:
            personas = self.loader.list_personas()
            if not personas:
                errors.append("No personas found in project")
                return GenerateResult(
                    success=False,
                    files_generated=files_generated,
                    errors=errors,
                )
            persona_name = personas[0]

        # Get output directory from config (already a Path)
        output_dir = self.config.generate.output_dir

        # Generate prompts for each action
        for action_name in actions:
            try:
                output_path = self.generator.generate(
                    action_name=action_name,
                    persona_name=persona_name,
                    output_dir=output_dir,
                    library=self.config.generate.library,
                    example_names=example_names,
                    prompt_config=self.config.prompts,
                )
                files_generated.append(output_path)

                # Generate variants if configured and action matches
                if self.config.prompts and action_name == self.config.prompts.action:
                    variant_files = self._generate_variants_for_prompt(
                        base_prompt_path=output_path,
                        base_action_name=action_name,
                        persona_name=persona_name,
                        example_names=example_names,
                        output_dir=output_dir,
                    )
                    files_generated.extend(variant_files)

            except Exception as e:
                errors.append(f"Failed to generate {action_name}: {e}")

        success = len(errors) == 0
        return GenerateResult(
            success=success,
            files_generated=files_generated,
            errors=errors,
        )

    def _generate_variants_for_prompt(
        self,
        base_prompt_path: Path,
        base_action_name: str,
        persona_name: str,
        example_names: list[str] | None,
        output_dir: Path,
    ) -> list[Path]:
        """Generate variants for a base prompt.

        For each variant, first attempts to generate directly from an action template
        (e.g., action/update-research.md.j2). If the action template doesn't exist,
        falls back to AI-based transformation using variant templates.

        Args:
            base_prompt_path: Path to the generated base prompt file
            base_action_name: Name of the base action (e.g., "research")
            persona_name: Persona name used for generation
            example_names: Example names to include
            output_dir: Output directory for variant files

        Returns:
            List of generated variant file paths
        """
        if self.config.prompts is None:
            return []

        variant_files: list[Path] = []

        for variant_name in self.config.prompts.variants:
            # Construct variant action name (e.g., "update-research")
            variant_action_name = f"{variant_name}-{base_action_name}"

            try:
                # Try to load and generate from action template
                self.loader.load_action(variant_action_name, persona_name)

                # If it exists, generate it as a normal action
                variant_path = self.generator.generate(
                    action_name=variant_action_name,
                    persona_name=persona_name,
                    output_dir=output_dir,
                    library=self.config.generate.library,
                    example_names=example_names,
                    prompt_config=self.config.prompts,
                )
                variant_files.append(variant_path)
                logger.info(
                    f"Generated variant '{variant_name}' from action template"
                )

            except ActionNotFoundError:
                # Fall back to AI-based variant generation
                try:
                    # Read the generated base prompt file
                    base_prompt = base_prompt_path.read_text()

                    # Get CLI tool
                    tool = self._get_cli_tool()

                    # Generate single variant using AI
                    variant_content = self.variant_generator.generate_single_variant(
                        variant_name=variant_name,
                        persona_name=persona_name,
                        action_name=base_action_name,
                        base_prompt=base_prompt,
                        tool=tool,
                        timeout=60,
                        prompt_config=self.config.prompts,
                    )

                    # Generate the variant action name and use the naming convention
                    # to create the proper filename (with library prefix if needed)
                    variant_action_name = f"{variant_name}-{base_action_name}"
                    variant_filename = self.naming.get_filename(
                        action_name=variant_action_name,
                        library=self.config.generate.library,
                    )
                    variant_path = output_dir / variant_filename
                    variant_path.write_text(variant_content)
                    variant_files.append(variant_path)
                    logger.info(
                        f"Generated variant '{variant_name}' using AI transformation"
                    )

                except Exception as e:
                    logger.error(f"Failed to generate variant {variant_name}: {e}")
                    # Continue with other variants

        return variant_files

    def _get_cli_tool(self) -> CLITool:
        """Get the CLI tool to use for AI-based variant generation.

        Returns:
            Selected CLI tool

        Raises:
            NoAvailableCLIToolError: If no CLI tools available
        """
        if self.config.prompts is None:
            raise ValueError("Prompts config is required")

        if self.config.prompts.cli_tool:
            # Use specific tool
            tool = get_tool_by_name(self.config.prompts.cli_tool)
            if tool is None or not tool.is_available():
                from pareidolia.core.exceptions import NoAvailableCLIToolError

                raise NoAvailableCLIToolError(
                    f"CLI tool not available: {self.config.prompts.cli_tool}"
                )
            return tool

        # Auto-detect available tools
        available = get_available_tools()
        if not available:
            from pareidolia.core.exceptions import NoAvailableCLIToolError

            raise NoAvailableCLIToolError(
                "No AI CLI tools available. Install one of: "
                "codex, gh copilot, claude, gemini"
            )

        return available[0]

    def generate_action(
        self,
        action_name: str,
        persona_name: str,
        example_names: list[str] | None = None,
    ) -> GenerateResult:
        """Generate a single action to a prompt file.

        Args:
            action_name: Name of the action to generate
            persona_name: Name of the persona to use
            example_names: Optional list of example names to include

        Returns:
            Generate result with generated file path and any errors
        """
        files_generated: list[Path] = []
        errors: list[str] = []

        # Get output directory from config (already a Path)
        output_dir = self.config.generate.output_dir

        try:
            output_path = self.generator.generate(
                action_name=action_name,
                persona_name=persona_name,
                output_dir=output_dir,
                library=self.config.generate.library,
                example_names=example_names,
                prompt_config=self.config.prompts,
            )
            files_generated.append(output_path)

            # Generate variants if configured and action matches
            if self.config.prompts and action_name == self.config.prompts.action:
                variant_files = self._generate_variants_for_prompt(
                    base_prompt_path=output_path,
                    base_action_name=action_name,
                    persona_name=persona_name,
                    example_names=example_names,
                    output_dir=output_dir,
                )
                files_generated.extend(variant_files)

        except Exception as e:
            errors.append(f"Failed to generate {action_name}: {e}")

        success = len(errors) == 0
        return GenerateResult(
            success=success,
            files_generated=files_generated,
            errors=errors,
        )
