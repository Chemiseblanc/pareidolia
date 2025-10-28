"""Component composition for complete prompts."""

from typing import Any

from pareidolia.core.models import Example, GenerateConfig, Persona, PromptConfig
from pareidolia.templates.engine import Jinja2Engine, TemplateEngine
from pareidolia.templates.loader import TemplateLoader


class PromptComposer:
    """Composes complete prompts from persona, action, and examples.

    Attributes:
        loader: Template loader for loading components
        engine: Template rendering engine
        generate_config: Optional generate configuration for tool/library context
    """

    def __init__(
        self,
        loader: TemplateLoader,
        engine: TemplateEngine | None = None,
        generate_config: GenerateConfig | None = None,
    ) -> None:
        """Initialize the prompt composer.

        Args:
            loader: Template loader
            engine: Template rendering engine (defaults to Jinja2Engine)
            generate_config: Optional generate configuration to expose
                tool and library context to templates
        """
        self.loader = loader
        self.engine = engine if engine is not None else Jinja2Engine()
        self.generate_config = generate_config

    def compose(
        self,
        action_name: str,
        persona_name: str,
        example_names: list[str] | None = None,
        prompt_config: PromptConfig | None = None,
    ) -> str:
        """Compose a complete prompt from components.

        Args:
            action_name: Name of the action template
            persona_name: Name of the persona
            example_names: Optional list of example names
            prompt_config: Optional prompt configuration for accessing metadata

        Returns:
            The rendered prompt

        Raises:
            PersonaNotFoundError: If the persona is not found
            ActionNotFoundError: If the action is not found
            TemplateRenderError: If rendering fails
        """
        # Load components
        persona = self.loader.load_persona(persona_name)
        action = self.loader.load_action(action_name, persona_name)

        examples: list[Example] = []
        if example_names:
            for example_name in example_names:
                examples.append(self.loader.load_example(example_name))

        # Build context
        context = self._build_context(persona, examples, prompt_config)

        # Render action template
        return self.engine.render(action.template, context)

    def _build_context(
        self,
        persona: Persona,
        examples: list[Example],
        prompt_config: PromptConfig | None = None,
    ) -> dict[str, Any]:
        """Build the template context.

        The context includes:
        - persona: The persona content
        - examples: Rendered examples (if provided)
        - tool: The target tool name (from generate_config, if available)
        - library: The library name (from generate_config, if available)
        - metadata: Metadata dictionary (from prompt_config, if available)

        Args:
            persona: The persona
            examples: List of examples
            prompt_config: Optional prompt configuration for metadata access

        Returns:
            Context dictionary for template rendering
        """
        context: dict[str, Any] = {
            "persona": persona.content,
        }

        # Add tool and library from generate_config if available
        if self.generate_config is not None:
            context["tool"] = self.generate_config.tool
            context["library"] = self.generate_config.library
        else:
            # Provide safe defaults for backward compatibility
            context["tool"] = "standard"
            context["library"] = None

        # Add metadata from prompt_config if available
        if prompt_config is not None:
            context["metadata"] = prompt_config.metadata
        else:
            # Default to empty dict for backward compatibility
            context["metadata"] = {}

        # Render examples if they are templates
        if examples:
            rendered_examples = []
            for example in examples:
                if example.is_template:
                    # Render example with current context
                    rendered = self.engine.render(example.content, context)
                    rendered_examples.append(rendered)
                else:
                    rendered_examples.append(example.content)

            context["examples"] = rendered_examples

        return context
