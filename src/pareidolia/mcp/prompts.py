"""MCP prompt definitions for Pareidolia prompts."""

import logging
from datetime import datetime
from typing import Any

from fastmcp import Context, FastMCP

from pareidolia.core.config import PareidoliaConfig
from pareidolia.generators.generator import Generator
from pareidolia.generators.variant_cache import CachedVariant, VariantCache
from pareidolia.templates.engine import Jinja2Engine

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
    """Register a variant prompt with sampling and caching.

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
        """Generate variant prompt with AI sampling.

        Args:
            ctx: FastMCP context for sampling

        Returns:
            Generated variant prompt content
        """
        # Check cache first
        cache = VariantCache()
        cached_variants = cache.get_by_action(action)

        for cached in cached_variants:
            if (
                cached.variant_name == variant
                and cached.persona_name == persona
                and cached.metadata == metadata
            ):
                logger.info(f"Using cached variant: {name}")
                return cached.content

        # Cache miss - generate using AI sampling
        logger.info(f"Generating variant: {name}")

        # First, generate the base prompt
        from pareidolia.core.models import PromptConfig

        prompt_config = PromptConfig(
            persona=persona,
            action=action,
            variants=["dummy"],
            metadata=metadata,
        )

        base_prompt = generator.composer.compose(
            action_name=action,
            persona_name=persona,
            example_names=examples,
            prompt_config=prompt_config,
        )

        # Load variant template
        try:
            variant_template_content = generator.loader.load_variant_template(variant)
        except Exception as e:
            logger.error(f"Failed to load variant template {variant}: {e}")
            raise RuntimeError(f"Variant template not found: {variant}") from e

        # Build context for variant template
        variant_context: dict[str, Any] = {
            "persona_name": persona,
            "action_name": action,
            "variant_name": variant,
            "tool": config.generate.tool,
            "library": config.generate.library,
            "metadata": metadata,
        }

        # Render variant template
        engine = Jinja2Engine()
        variant_instruction = engine.render(variant_template_content, variant_context)

        # Create the complete prompt for sampling
        sampling_prompt = (
            f"{variant_instruction}\n\n# Base Prompt to Transform\n\n{base_prompt}"
        )

        # Use ctx.sample() to generate the variant
        try:
            response = await ctx.sample(sampling_prompt)
            # SamplingResponse has .text attribute with the generated content
            variant_content: str = response.text  # type: ignore[union-attr]
        except Exception as e:
            logger.error(f"Failed to sample variant {name}: {e}")
            raise RuntimeError(f"Variant generation failed: {e}") from e

        # Cache the result
        cached_variant = CachedVariant(
            variant_name=variant,
            action_name=action,
            persona_name=persona,
            content=variant_content,
            generated_at=datetime.now(),
            metadata=metadata,
        )
        cache.add(cached_variant)
        logger.info(f"Cached variant: {name}")

        return variant_content

    # Set function metadata
    variant_prompt.__name__ = name.replace("-", "_")
    variant_prompt.__doc__ = (
        f"Generate {variant} variant of {action} prompt for {persona} persona."
    )

    # Register the prompt
    mcp.prompt()(variant_prompt)
