"""Component composition for complete prompts."""

from typing import Any

from pareidolia.core.models import Example, Persona
from pareidolia.templates.engine import Jinja2Engine, TemplateEngine
from pareidolia.templates.loader import TemplateLoader


class PromptComposer:
    """Composes complete prompts from persona, action, and examples.

    Attributes:
        loader: Template loader for loading components
        engine: Template rendering engine
    """

    def __init__(
        self,
        loader: TemplateLoader,
        engine: TemplateEngine | None = None,
    ) -> None:
        """Initialize the prompt composer.

        Args:
            loader: Template loader
            engine: Template rendering engine (defaults to Jinja2Engine)
        """
        self.loader = loader
        self.engine = engine if engine is not None else Jinja2Engine()

    def compose(
        self,
        action_name: str,
        persona_name: str,
        example_names: list[str] | None = None,
    ) -> str:
        """Compose a complete prompt from components.

        Args:
            action_name: Name of the action template
            persona_name: Name of the persona
            example_names: Optional list of example names

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
        context = self._build_context(persona, examples)

        # Render action template
        return self.engine.render(action.template, context)

    def _build_context(
        self,
        persona: Persona,
        examples: list[Example],
    ) -> dict[str, Any]:
        """Build the template context.

        Args:
            persona: The persona
            examples: List of examples

        Returns:
            Context dictionary for template rendering
        """
        context: dict[str, Any] = {
            "persona": persona.content,
        }

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
