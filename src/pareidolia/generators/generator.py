"""Generate functionality for generating multiple prompts."""

import logging
from dataclasses import dataclass
from pathlib import Path

from pareidolia.core.config import PareidoliaConfig
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
        self.composer = PromptComposer(self.loader, Jinja2Engine())

        naming = get_naming_convention(config.generate.tool)
        self.generator = PromptGenerator(self.composer, naming)
        self.variant_generator = VariantGenerator(self.loader, self.composer)

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
                )
                files_generated.append(output_path)

                # Generate variants if configured and action matches
                if self.config.prompts and action_name == self.config.prompts.action:
                    variant_files = self._generate_variants_for_prompt(
                        base_prompt_path=output_path,
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
        output_dir: Path,
    ) -> list[Path]:
        """Generate variants for a base prompt.

        Args:
            base_prompt_path: Path to the generated base prompt file
            output_dir: Output directory for variant files

        Returns:
            List of generated variant file paths
        """
        if self.config.prompts is None:
            return []

        variant_files: list[Path] = []

        try:
            # Read the generated base prompt file
            base_prompt = base_prompt_path.read_text()

            # Extract base filename without extension
            base_filename = base_prompt_path.stem

            # Generate all variants
            variants = self.variant_generator.generate_variants(
                prompt_config=self.config.prompts,
                base_prompt=base_prompt,
            )

            # Write each variant to file using verb-noun naming
            for variant_name, variant_content in variants.items():
                # Use verb-noun naming: update-research.md
                variant_filename = f"{variant_name}-{base_filename}.md"
                variant_path = output_dir / variant_filename

                variant_path.write_text(variant_content)
                variant_files.append(variant_path)
                logger.info(f"Generated variant file: {variant_filename}")

        except Exception as e:
            # Log error but don't fail the entire generation
            logger.error(f"Failed to generate variants: {e}")

        return variant_files

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
            )
            files_generated.append(output_path)

            # Generate variants if configured and action matches
            if self.config.prompts and action_name == self.config.prompts.action:
                variant_files = self._generate_variants_for_prompt(
                    base_prompt_path=output_path,
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
