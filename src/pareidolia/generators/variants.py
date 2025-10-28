"""Variant generation orchestration."""

import logging

from pareidolia.core.exceptions import (
    NoAvailableCLIToolError,
    VariantTemplateNotFoundError,
)
from pareidolia.core.models import VariantConfig
from pareidolia.generators.cli_tools import (
    CLITool,
    get_available_tools,
    get_tool_by_name,
)
from pareidolia.templates.composer import PromptComposer
from pareidolia.templates.engine import Jinja2Engine
from pareidolia.templates.loader import TemplateLoader

logger = logging.getLogger(__name__)


class VariantGenerator:
    """Generates prompt variants using AI CLI tools.

    Attributes:
        loader: Template loader
        composer: Prompt composer
        engine: Template engine
    """

    def __init__(
        self,
        loader: TemplateLoader,
        composer: PromptComposer,
    ) -> None:
        """Initialize variant generator.

        Args:
            loader: Template loader for variant templates
            composer: Prompt composer for rendering
        """
        self.loader = loader
        self.composer = composer
        self.engine = Jinja2Engine()

    def generate_variants(
        self,
        variant_config: VariantConfig,
        base_prompt: str,
        timeout: int = 60,
    ) -> dict[str, str]:
        """Generate all configured variants.

        Args:
            variant_config: Variant configuration
            base_prompt: Base prompt content to transform
            timeout: CLI tool timeout in seconds

        Returns:
            Dictionary mapping variant names to generated content

        Raises:
            NoAvailableCLIToolError: If no CLI tools available
            VariantTemplateNotFoundError: If variant template missing
        """
        # Determine which tool to use
        tool = self._select_tool(variant_config.cli_tool)

        variants: dict[str, str] = {}

        # Generate each variant
        for variant_name in variant_config.generate:
            try:
                variant_content = self._generate_single_variant(
                    variant_name=variant_name,
                    persona_name=variant_config.persona,
                    action_name=variant_config.action,
                    base_prompt=base_prompt,
                    tool=tool,
                    timeout=timeout,
                )
                variants[variant_name] = variant_content
                logger.info(f"Generated variant: {variant_name}")
            except VariantTemplateNotFoundError as e:
                logger.warning(f"Skipping variant {variant_name}: {e}")
            except Exception as e:
                logger.error(
                    f"Failed to generate variant {variant_name}: {e}"
                )
                # Continue with other variants

        return variants

    def _select_tool(self, requested_tool: str | None) -> CLITool:
        """Select CLI tool to use.

        Args:
            requested_tool: Requested tool name or None for auto-detect

        Returns:
            Selected CLI tool

        Raises:
            NoAvailableCLIToolError: If no tools available
        """
        if requested_tool:
            # Use specific tool
            tool = get_tool_by_name(requested_tool)
            if tool is None:
                raise NoAvailableCLIToolError(
                    f"CLI tool not found: {requested_tool}"
                )
            if not tool.is_available():
                raise NoAvailableCLIToolError(
                    f"CLI tool not available: {requested_tool}"
                )
            return tool

        # Auto-detect available tools
        available = get_available_tools()
        if not available:
            raise NoAvailableCLIToolError(
                "No AI CLI tools available. Install one of: "
                "codex, gh copilot, claude, gemini"
            )

        selected = available[0]
        logger.info(f"Using CLI tool: {selected.name}")
        return selected

    def _generate_single_variant(
        self,
        variant_name: str,
        persona_name: str,
        action_name: str,
        base_prompt: str,
        tool: CLITool,
        timeout: int,
    ) -> str:
        """Generate a single variant.

        Args:
            variant_name: Name of the variant
            persona_name: Persona name for context
            action_name: Action name for context
            base_prompt: Base prompt to transform
            tool: CLI tool to use
            timeout: Timeout in seconds

        Returns:
            Generated variant content

        Raises:
            VariantTemplateNotFoundError: If template not found
            CLIToolError: If generation fails
        """
        # Load and render variant template
        template_content = self.loader.load_variant_template(variant_name)

        # Render template with context
        context = {
            "persona_name": persona_name,
            "action_name": action_name,
            "variant_name": variant_name,
        }
        variant_prompt = self.engine.render(template_content, context)

        # Generate variant using CLI tool
        return tool.generate_variant(
            variant_prompt=variant_prompt,
            base_prompt=base_prompt,
            timeout=timeout,
        )
