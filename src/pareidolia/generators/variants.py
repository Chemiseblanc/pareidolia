"""Variant generation orchestration."""

import logging
from pathlib import Path
from typing import Any, Literal

from pareidolia.core.exceptions import (
    ActionNotFoundError,
    CLIToolError,
    NoAvailableCLIToolError,
)
from pareidolia.core.models import GenerateConfig
from pareidolia.generators.cli_tools import (
    CLITool,
    get_available_tools,
    get_tool_by_name,
)
from pareidolia.templates.composer import PromptComposer
from pareidolia.templates.engine import Jinja2Engine
from pareidolia.templates.loader import TemplateLoader

logger = logging.getLogger(__name__)

MAX_TEMPLATE_GENERATION_RETRIES = 3


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

    # NOTE: generate_variants method removed - incompatible with new
    # template-based approach. Variants are now generated as action templates,
    # not final prompts. Callers should use generate_single_variant directly
    # or be updated accordingly.

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
        action_name: str,
        persona_name: str,
        strategy: Literal["cli", "mcp"] = "cli",
        ctx: Any | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Path:
        """Generate a single variant action template using AI transformation.

        This method generates a variant action template (Jinja2 .md.j2 file) instead
        of a final prompt. The generated template preserves placeholders like
        {{ persona }}, {{ tool }}, {{ library }} from the base action template.

        Args:
            variant_name: Name of the variant (e.g., "refine", "summarize")
            action_name: Name of the action to create variant for (e.g., "research")
            persona_name: Name of the persona (for loading base template)
            strategy: Generation strategy - "cli" for subprocess or "mcp" for sampling
            ctx: Context object for MCP sampling (required if strategy="mcp")
            metadata: Optional metadata dict to include in variant instruction rendering

        Returns:
            Path to the created variant action template file

        Raises:
            ActionNotFoundError: If base action template not found
            VariantTemplateNotFoundError: If variant instruction template not found
            CLIToolError: If AI generation fails after retries
            NoAvailableCLIToolError: If no CLI tools available (strategy="cli")
            ValueError: If strategy="mcp" but ctx is None
        """
        # Load base action TEMPLATE (not rendered with persona)
        try:
            # Load action template
            action = self.loader.load_action(action_name, persona_name)
            base_template_content = action.template
        except ActionNotFoundError:
            raise

        # Load variant instruction template
        variant_instructions = self.loader.load_variant_template(variant_name)

        # Render variant instructions with context
        context: dict[str, Any] = {
            "persona_name": "placeholder",  # Not used in output template
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

        # Add metadata for rendering
        context["metadata"] = metadata if metadata is not None else {}

        # Render variant instructions
        rendered_variant_instructions = self.engine.render(
            variant_instructions, context
        )

        # Build prompt for AI to generate template
        base_instruction = (
            "You must generate a Jinja2 template file. "
            "Preserve ALL Jinja2 placeholders like {{ persona }}, {{ tool }}, "
            "{{ library }} exactly as they appear in the base template."
        )

        ai_prompt = (
            f"{base_instruction}\n\n"
            f"{rendered_variant_instructions}\n\n"
            f"Base template:\n{base_template_content}"
        )

        # Generate template with retries
        generated_template: str | None = None
        for attempt in range(MAX_TEMPLATE_GENERATION_RETRIES):
            if attempt > 0:
                # Add retry instruction
                retry_instruction = (
                    "Template validation failed, ensure all Jinja2 placeholders "
                    "like {{ persona }}, {{ tool }}, {{ library }} are preserved "
                    "exactly as they appear."
                )
                current_prompt = f"{retry_instruction}\n\n{ai_prompt}"
            else:
                current_prompt = ai_prompt

            # Call AI based on strategy
            try:
                if strategy == "cli":
                    tool = self._select_tool(None)  # Auto-select tool
                    generated_template = tool.generate_variant(
                        variant_prompt=current_prompt,
                        base_prompt="",
                        timeout=60,
                    )
                elif strategy == "mcp":
                    if ctx is None:
                        raise ValueError(
                            "ctx parameter required for mcp strategy"
                        )
                    # Import here to avoid dependency when not using MCP
                    # ctx.sample() is async but we're in sync context
                    # This will need to be called from an async context
                    import asyncio

                    # Get or create event loop
                    try:
                        loop = asyncio.get_event_loop()
                    except RuntimeError:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)

                    # Call async sample method
                    response = loop.run_until_complete(
                        ctx.sample(current_prompt)
                    )
                    # SamplingResponse has .text attribute
                    generated_template = response.text
                else:
                    raise ValueError(f"Unknown strategy: {strategy}")

            except (CLIToolError, NoAvailableCLIToolError) as e:
                if attempt == MAX_TEMPLATE_GENERATION_RETRIES - 1:
                    raise
                logger.warning(
                    f"AI generation attempt {attempt + 1} failed: {e}"
                )
                continue

            # Validate generated template
            if generated_template and "{{ persona }}" in generated_template:
                break
            else:
                logger.warning(
                    f"Generated template missing {{ persona }} placeholder "
                    f"(attempt {attempt + 1})"
                )
                generated_template = None

        if generated_template is None:
            raise CLIToolError(
                f"Failed to generate valid template for {variant_name}-{action_name} "
                f"after {MAX_TEMPLATE_GENERATION_RETRIES} attempts"
            )

        # Write template to actions/{variant}-{action}.md.j2
        actions_dir = self.loader.root / "actions"
        actions_dir.mkdir(parents=True, exist_ok=True)

        template_filename = f"{variant_name}-{action_name}.md.j2"
        template_path = actions_dir / template_filename

        template_path.write_text(generated_template)
        logger.info(f"Created variant template: {template_path}")

        return template_path
