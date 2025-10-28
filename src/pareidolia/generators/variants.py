"""Variant generation orchestration."""

import logging
from typing import Any

from pareidolia.core.exceptions import (
    NoAvailableCLIToolError,
    VariantTemplateNotFoundError,
)
from pareidolia.core.models import GenerateConfig, PromptConfig
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
        generate_config: Optional generate configuration for context
    """

    def __init__(
        self,
        loader: TemplateLoader,
        composer: PromptComposer,
        generate_config: GenerateConfig | None = None,
    ) -> None:
        """Initialize variant generator.

        Args:
            loader: Template loader for variant templates
            composer: Prompt composer for rendering
            generate_config: Optional generate configuration for tool/library context
        """
        self.loader = loader
        self.composer = composer
        self.engine = Jinja2Engine()
        self.generate_config = generate_config

    def generate_variants(
        self,
        prompt_config: PromptConfig,
        base_prompt: str,
        timeout: int = 60,
    ) -> dict[str, str]:
        """Generate all configured variants.

        Args:
            prompt_config: Prompt variant configuration
            base_prompt: Base prompt content to transform
            timeout: CLI tool timeout in seconds

        Returns:
            Dictionary mapping variant names to generated content

        Raises:
            NoAvailableCLIToolError: If no CLI tools available
            VariantTemplateNotFoundError: If variant template missing
        """
        # Determine which tool to use
        tool = self._select_tool(prompt_config.cli_tool)

        variants: dict[str, str] = {}

        # Generate each variant
        for variant_name in prompt_config.variants:
            try:
                variant_content = self.generate_single_variant(
                    variant_name=variant_name,
                    persona_name=prompt_config.persona,
                    action_name=prompt_config.action,
                    base_prompt=base_prompt,
                    tool=tool,
                    timeout=timeout,
                    prompt_config=prompt_config,
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

    def generate_single_variant(
        self,
        variant_name: str,
        persona_name: str,
        action_name: str,
        base_prompt: str,
        tool: CLITool,
        timeout: int,
        prompt_config: PromptConfig | None = None,
    ) -> str:
        """Generate a single variant using AI transformation.

        Args:
            variant_name: Name of the variant
            persona_name: Persona name for context
            action_name: Action name for context
            base_prompt: Base prompt to transform
            tool: CLI tool to use
            timeout: Timeout in seconds
            prompt_config: Optional prompt configuration for metadata access

        Returns:
            Generated variant content

        Raises:
            VariantTemplateNotFoundError: If template not found
            CLIToolError: If generation fails
        """
        # Load and render variant template
        template_content = self.loader.load_variant_template(variant_name)

        # Build context with all available information
        context: dict[str, Any] = {
            "persona_name": persona_name,
            "action_name": action_name,
            "variant_name": variant_name,
        }

        # Add tool and library from generate_config if available
        if self.generate_config is not None:
            context["tool"] = self.generate_config.tool
            context["library"] = self.generate_config.library
        else:
            context["tool"] = "standard"
            context["library"] = None

        # Add metadata from prompt_config if available
        if prompt_config is not None:
            context["metadata"] = prompt_config.metadata
        else:
            context["metadata"] = {}

        # Render template with context
        variant_prompt = self.engine.render(template_content, context)

        # Generate variant using CLI tool
        return tool.generate_variant(
            variant_prompt=variant_prompt,
            base_prompt=base_prompt,
            timeout=timeout,
        )
