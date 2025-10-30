"""MCP prompt definitions for Pareidolia prompts."""

import logging
from typing import Any

from fastmcp import Context, FastMCP

from pareidolia.core.config import PareidoliaConfig
from pareidolia.core.exceptions import ActionNotFoundError
from pareidolia.generators.generator import Generator

logger = logging.getLogger(__name__)


def discover_prompts(
    config: PareidoliaConfig,
) -> list[tuple[str, str, str, list[str] | None, dict[str, Any], str | None]]:
    """Discover all prompts from configuration.

    Iterates through config.prompt to build a list of prompt definitions.
    Each prompt includes both the base action and all configured variants.

    Args:
        config: Pareidolia configuration

    Returns:
        List of tuples containing:
        (name, persona, action, examples, metadata, variant)
        - name: Prompt name (action for base, variant-action for variants)
        - persona: Persona name
        - action: Action name
        - examples: Optional list of example names
        - metadata: Metadata dictionary
        - variant: Variant name (None for base prompts)
    """
    prompts: list[
        tuple[str, str, str, list[str] | None, dict[str, Any], str | None]
    ] = []

    if not config.prompt:
        # No prompts configured - return empty list
        logger.warning("No prompts configured in configuration")
        return prompts

    for prompt_config in config.prompt:
        # Add base prompt
        base_name = prompt_config.action
        prompts.append(
            (
                base_name,
                prompt_config.persona,
                prompt_config.action,
                None,  # No examples by default (can be added later if needed)
                prompt_config.metadata,
                None,  # No variant for base prompt
            )
        )

        # Add variant prompts
        for variant_name in prompt_config.variants:
            variant_prompt_name = f"{variant_name}-{prompt_config.action}"
            prompts.append(
                (
                    variant_prompt_name,
                    prompt_config.persona,
                    prompt_config.action,
                    None,  # No examples by default
                    prompt_config.metadata,
                    variant_name,
                )
            )

    return prompts


def register_prompts(
    mcp: FastMCP,
    generator: Generator,
    config: PareidoliaConfig,
) -> None:
    """Register all MCP prompts with the server.

    Creates prompt functions dynamically for each discovered prompt and
    registers them using FastMCP's @mcp.prompt() decorator.

    Args:
        mcp: FastMCP server instance
        generator: Prompt generator instance
        config: Pareidolia configuration
    """
    # Discover all prompts
    prompts = discover_prompts(config)

    if not prompts:
        logger.info("No prompts to register")
        return

    logger.info(f"Registering {len(prompts)} prompts")

    # Register each prompt
    for name, persona, action, examples, metadata, variant in prompts:
        if variant is None:
            # Base prompt - synchronous, no sampling needed
            _register_base_prompt(
                mcp, generator, name, persona, action, examples, metadata
            )
        else:
            # Variant prompt - asynchronous with sampling and caching
            _register_variant_prompt(
                mcp,
                generator,
                config,
                name,
                persona,
                action,
                examples,
                metadata,
                variant,
            )

        logger.debug(f"Registered prompt: {name}")


def _register_base_prompt(
    mcp: FastMCP,
    generator: Generator,
    name: str,
    persona: str,
    action: str,
    examples: list[str] | None,
    metadata: dict[str, Any],
) -> None:
    """Register a base prompt.

    Args:
        mcp: FastMCP server instance
        generator: Prompt generator instance
        name: Prompt name
        persona: Persona name
        action: Action name
        examples: Optional list of example names
        metadata: Metadata dictionary
    """

    def base_prompt() -> str:
        """Generate base prompt.

        Returns:
            Generated prompt content
        """
        # Create prompt config for metadata access
        from pareidolia.core.models import PromptConfig

        # Use a dummy variant to satisfy validation (won't be used)
        prompt_config = PromptConfig(
            persona=persona,
            action=action,
            variants=["dummy"],
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

    # Set function metadata
    base_prompt.__name__ = name.replace("-", "_")
    base_prompt.__doc__ = f"Generate {name} prompt for {persona} persona."

    # Register the prompt
    mcp.prompt()(base_prompt)


def _register_variant_prompt(
    mcp: FastMCP,
    generator: Generator,
    config: PareidoliaConfig,
    name: str,
    persona: str,
    action: str,
    examples: list[str] | None,
    metadata: dict[str, Any],
    variant: str,
) -> None:
    """Register a variant prompt using template-first architecture.

    First attempts to compose the variant prompt from an existing template.
    If the template doesn't exist, generates it on-the-fly using AI sampling,
    then composes from the newly created template.

    Args:
        mcp: FastMCP server instance
        generator: Prompt generator instance
        config: Pareidolia configuration
        name: Prompt name (variant-action format)
        persona: Persona name
        action: Action name
        examples: Optional list of example names
        metadata: Metadata dictionary
        variant: Variant name
    """

    async def variant_prompt(ctx: Context) -> str:
        """Generate variant prompt from template or create template on-the-fly.

        Args:
            ctx: FastMCP context for template generation if needed

        Returns:
            Composed variant prompt content
        """
        from pareidolia.core.models import PromptConfig

        # Create prompt config for composition
        prompt_config = PromptConfig(
            persona=persona,
            action=action,
            variants=["dummy"],
            metadata=metadata,
        )

        # Try to compose variant prompt from existing template
        variant_action = f"{variant}-{action}"
        try:
            prompt = generator.composer.compose(
                action_name=variant_action,
                persona_name=persona,
                example_names=examples,
                prompt_config=prompt_config,
            )
            return prompt

        except ActionNotFoundError:
            # Template doesn't exist - generate it
            logger.info(
                f"Template for {variant_action} not found, generating it"
            )

            # Generate the variant action template using async context
            try:
                # Call generate_single_variant with mcp strategy
                # Note: This is synchronous but handles async internally via ctx
                generator.variant_generator.generate_single_variant(
                    variant_name=variant,
                    action_name=action,
                    persona_name=persona,
                    strategy="mcp",
                    ctx=ctx,
                    metadata=metadata,
                )
                logger.info(f"Generated template for {variant_action}")

            except Exception as e:
                logger.error(f"Failed to generate template {variant_action}: {e}")
                raise RuntimeError(
                    f"Template generation failed for {variant_action}: {e}"
                ) from e

            # Now compose from the newly created template
            try:
                prompt = generator.composer.compose(
                    action_name=variant_action,
                    persona_name=persona,
                    example_names=examples,
                    prompt_config=prompt_config,
                )
                return prompt

            except Exception as e:
                logger.error(
                    f"Failed to compose {variant_action} after generation: {e}"
                )
                raise RuntimeError(
                    f"Composition failed for {variant_action}: {e}"
                ) from e

    # Set function metadata
    variant_prompt.__name__ = name.replace("-", "_")
    variant_prompt.__doc__ = (
        f"Generate {variant} variant of {action} prompt for {persona} persona."
    )

    # Register the prompt
    mcp.prompt()(variant_prompt)
