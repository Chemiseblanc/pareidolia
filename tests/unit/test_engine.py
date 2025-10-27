"""Unit tests for template engine."""

import pytest

from pareidolia.core.exceptions import TemplateRenderError
from pareidolia.templates.engine import Jinja2Engine


class TestJinja2Engine:
    """Tests for Jinja2 template engine."""

    def test_render_simple_template(self) -> None:
        """Test rendering a simple template."""
        engine = Jinja2Engine()
        template = "Hello, {{ name }}!"
        context = {"name": "World"}

        result = engine.render(template, context)
        assert result == "Hello, World!"

    def test_render_with_multiple_variables(self) -> None:
        """Test rendering with multiple variables."""
        engine = Jinja2Engine()
        template = "{{ greeting }}, {{ name }}!"
        context = {"greeting": "Hello", "name": "World"}

        result = engine.render(template, context)
        assert result == "Hello, World!"

    def test_render_with_conditionals(self) -> None:
        """Test rendering with conditional logic."""
        engine = Jinja2Engine()
        template = (
            "{% if show_message %}"
            "Message: {{ message }}"
            "{% endif %}"
        )

        result = engine.render(template, {"show_message": True, "message": "Hello"})
        assert result == "Message: Hello"

        result = engine.render(template, {"show_message": False, "message": "Hello"})
        assert result == ""

    def test_render_with_loops(self) -> None:
        """Test rendering with loops."""
        engine = Jinja2Engine()
        template = (
            "{% for item in items %}"
            "- {{ item }}\\n"
            "{% endfor %}"
        )
        context = {"items": ["one", "two", "three"]}

        result = engine.render(template, context)
        assert "- one" in result
        assert "- two" in result
        assert "- three" in result

    def test_render_preserves_trailing_newline(self) -> None:
        """Test that trailing newlines are preserved."""
        engine = Jinja2Engine()
        template = "Content\\n"

        result = engine.render(template, {})
        assert result == "Content\\n"

    def test_render_with_missing_variable(self) -> None:
        """Test that missing variables are handled (rendered as empty)."""
        engine = Jinja2Engine()
        template = "Hello, {{ name }}!"

        result = engine.render(template, {})
        assert result == "Hello, !"

    def test_render_with_syntax_error(self) -> None:
        """Test that syntax errors raise TemplateRenderError."""
        engine = Jinja2Engine()
        template = "{% if unclosed %}"

        with pytest.raises(TemplateRenderError, match="syntax error"):
            engine.render(template, {})

    def test_render_with_undefined_error(self) -> None:
        """Test that undefined errors in strict mode are caught."""
        engine = Jinja2Engine()
        # This template will fail if we try to call a method on undefined
        template = "{{ items.invalid_method() }}"

        with pytest.raises(TemplateRenderError):
            engine.render(template, {})

    def test_no_autoescape(self) -> None:
        """Test that HTML is not escaped."""
        engine = Jinja2Engine()
        template = "{{ html }}"
        context = {"html": "<p>Hello</p>"}

        result = engine.render(template, context)
        assert result == "<p>Hello</p>"
