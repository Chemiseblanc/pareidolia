"""Jinja2 template rendering engine for pareidolia."""

from typing import Any, Protocol

from jinja2 import Environment, Template, TemplateSyntaxError

from pareidolia.core.exceptions import TemplateRenderError


class TemplateEngine(Protocol):
    """Protocol for template rendering engines."""

    def render(self, template: str, context: dict[str, Any]) -> str:
        """Render a template with the given context.

        Args:
            template: The template string
            context: Variables to use in rendering

        Returns:
            The rendered template

        Raises:
            TemplateRenderError: If rendering fails
        """
        ...


class Jinja2Engine:
    """Jinja2-based template rendering engine."""

    def __init__(self) -> None:
        """Initialize the Jinja2 engine."""
        self.env = Environment(
            autoescape=False,
            keep_trailing_newline=True,
        )

    def render(self, template: str, context: dict[str, Any]) -> str:
        """Render a Jinja2 template with the given context.

        Args:
            template: The Jinja2 template string
            context: Variables to use in rendering

        Returns:
            The rendered template

        Raises:
            TemplateRenderError: If template syntax is invalid or rendering fails
        """
        try:
            tmpl: Template = self.env.from_string(template)
            return tmpl.render(context)
        except TemplateSyntaxError as e:
            raise TemplateRenderError(
                f"Template syntax error at line {e.lineno}: {e.message}"
            ) from e
        except Exception as e:
            raise TemplateRenderError(f"Template rendering failed: {e}") from e
