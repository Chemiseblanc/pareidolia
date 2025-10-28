"""MCP tool definitions for Pareidolia prompts."""

from typing import Any

from fastmcp import Context, FastMCP

from pareidolia.core.config import PareidoliaConfig
from pareidolia.core.exceptions import (
    ActionNotFoundError,
    PareidoliaError,
    PersonaNotFoundError,
)
from pareidolia.core.models import PromptConfig
from pareidolia.generators.generator import Generator


def register_tools(
    mcp: FastMCP,
    generator: Generator,
    config: PareidoliaConfig,
) -> None:
    """Register all MCP tools with the server.

    Args:
        mcp: FastMCP server instance
        generator: Prompt generator instance
        config: Pareidolia configuration
    """

    @mcp.tool()
    def list_personas() -> list[dict[str, str]]:
        """List all available personas.

        Returns:
            List of dictionaries with persona names and content previews

        Raises:
            RuntimeError: If personas cannot be loaded
        """
        try:
            persona_names = generator.loader.list_personas()
            result = []

            for name in persona_names:
                try:
                    persona = generator.loader.load_persona(name)
                    result.append({
                        "name": persona.name,
                        "content_preview": persona.content[:200] + "..."
                        if len(persona.content) > 200
                        else persona.content,
                    })
                except Exception:
                    # Skip personas that can't be loaded
                    continue

            return result
        except Exception as e:
            raise RuntimeError(f"Failed to list personas: {e}") from e

    @mcp.tool()
    def list_actions(persona_name: str) -> list[dict[str, str]]:
        """List all available actions for a given persona.

        Args:
            persona_name: Name of the persona

        Returns:
            List of dictionaries with action names and template previews

        Raises:
            ValueError: If persona is not found
            RuntimeError: If actions cannot be loaded
        """
        try:
            # First verify persona exists
            generator.loader.load_persona(persona_name)

            # Get all action names
            action_names = generator.loader.list_actions()
            result = []

            # Try to load each action for this persona
            for name in action_names:
                try:
                    action = generator.loader.load_action(name, persona_name)
                    result.append({
                        "name": action.name,
                        "template_preview": action.template[:200] + "..."
                        if len(action.template) > 200
                        else action.template,
                    })
                except Exception:
                    # Skip actions that don't exist for this persona
                    continue

            return result
        except PersonaNotFoundError as e:
            raise ValueError(f"Persona not found: {e}") from e
        except Exception as e:
            raise RuntimeError(f"Failed to list actions: {e}") from e

    @mcp.tool()
    def list_examples() -> list[dict[str, str]]:
        """List all available examples.

        Returns:
            List of dictionaries with example names and content previews

        Raises:
            RuntimeError: If examples cannot be loaded
        """
        try:
            example_names = generator.loader.list_examples()
            result = []

            for name in example_names:
                try:
                    example = generator.loader.load_example(name)
                    result.append({
                        "name": example.name,
                        "content_preview": example.content[:200] + "..."
                        if len(example.content) > 200
                        else example.content,
                        "is_template": str(example.is_template),
                    })
                except Exception:
                    # Skip examples that can't be loaded
                    continue

            return result
        except Exception as e:
            raise RuntimeError(f"Failed to list examples: {e}") from e

    @mcp.tool()
    def generate_prompt(
        action: str,
        persona: str,
        examples: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Generate a single prompt from components.

        Args:
            action: Name of the action to generate
            persona: Name of the persona to use
            examples: Optional list of example names to include
            metadata: Optional metadata dictionary for the prompt

        Returns:
            Generated prompt content

        Raises:
            ValueError: If persona or action not found
            RuntimeError: If generation fails
        """
        try:
            # Create a temporary prompt config if metadata provided
            # Note: We use a dummy variant to satisfy PromptConfig validation
            # but don't actually generate variants
            prompt_config = None
            if metadata is not None:
                prompt_config = PromptConfig(
                    persona=persona,
                    action=action,
                    variants=["dummy"],  # Dummy variant to satisfy validation
                    metadata=metadata,
                )

            # Compose the prompt
            prompt = generator.composer.compose(
                action_name=action,
                persona_name=persona,
                example_names=examples,
                prompt_config=prompt_config,
            )

            return prompt

        except PersonaNotFoundError as e:
            raise ValueError(f"Persona not found: {e}") from e
        except ActionNotFoundError as e:
            raise ValueError(f"Action not found: {e}") from e
        except PareidoliaError as e:
            raise RuntimeError(f"Generation failed: {e}") from e
        except Exception as e:
            raise RuntimeError(f"Unexpected error: {e}") from e

    @mcp.tool()
    def generate_with_sampler(
        action: str,
        persona: str,
        examples: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        ctx: Context | None = None,
    ) -> str:
        """Generate a prompt with optional AI enhancement via sampler.

        This tool supports the FastMCP sampler feature for AI-enhanced
        prompt generation. When used with a sampler, it can provide
        AI-powered suggestions and improvements.

        Args:
            action: Name of the action to generate
            persona: Name of the persona to use
            examples: Optional list of example names to include
            metadata: Optional metadata dictionary for the prompt
            ctx: FastMCP context (automatically provided by MCP)

        Returns:
            Generated prompt content (potentially AI-enhanced)

        Raises:
            ValueError: If persona or action not found
            RuntimeError: If generation fails
        """
        # First, generate the base prompt
        base_prompt: str = generate_prompt(action, persona, examples, metadata)  # type: ignore[operator]

        # If context with sampler is available, could enhance further
        # For now, just return the base prompt
        # Future: Use ctx.sample() for AI enhancement
        return base_prompt

    @mcp.tool()
    def generate_variants(
        action: str,
        persona: str,
        variants: list[str],
        examples: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        cli_tool: str | None = None,
        timeout: int = 60,
    ) -> dict[str, str]:
        """Generate prompt variants from a base action.

        Variants can be generated from action templates (e.g., 'update-research')
        or through AI transformation using variant templates.

        Args:
            action: Name of the base action
            persona: Name of the persona to use
            variants: List of variant names to generate (e.g., ['update', 'refine'])
            examples: Optional list of example names to include
            metadata: Optional metadata dictionary for the prompts
            cli_tool: Optional specific CLI tool for AI generation
            timeout: Timeout in seconds for AI generation (default: 60)

        Returns:
            Dictionary mapping variant names to generated content

        Raises:
            ValueError: If persona or action not found, or variants list is empty
            RuntimeError: If generation fails
        """
        if not variants:
            raise ValueError("Variants list cannot be empty")

        try:
            # Create prompt config
            prompt_config = PromptConfig(
                persona=persona,
                action=action,
                variants=variants,
                cli_tool=cli_tool,
                metadata=metadata or {},
            )

            # Generate base prompt first
            base_prompt: str = generate_prompt(action, persona, examples, metadata)  # type: ignore[operator]

            # Generate variants
            variant_results = generator.variant_generator.generate_variants(
                prompt_config=prompt_config,
                base_prompt=base_prompt,
                timeout=timeout,
            )

            return variant_results

        except PersonaNotFoundError as e:
            raise ValueError(f"Persona not found: {e}") from e
        except ActionNotFoundError as e:
            raise ValueError(f"Action not found: {e}") from e
        except PareidoliaError as e:
            raise RuntimeError(f"Variant generation failed: {e}") from e
        except Exception as e:
            raise RuntimeError(f"Unexpected error: {e}") from e

    @mcp.tool()
    def compose_prompt(
        action: str,
        persona: str,
        examples: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Compose a prompt from components (alias for generate_prompt).

        This is a semantic alias for generate_prompt that emphasizes
        the composition aspect of combining persona, action, and examples.

        Args:
            action: Name of the action to generate
            persona: Name of the persona to use
            examples: Optional list of example names to include
            metadata: Optional metadata dictionary for the prompt

        Returns:
            Composed prompt content

        Raises:
            ValueError: If persona or action not found
            RuntimeError: If composition fails
        """
        result: str = generate_prompt(action, persona, examples, metadata)  # type: ignore[operator]
        return result
