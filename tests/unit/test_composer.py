"""Unit tests for PromptComposer."""

from pathlib import Path
from unittest.mock import Mock

import pytest

from pareidolia.core.models import (
    Action,
    Example,
    GenerateConfig,
    Persona,
    PromptConfig,
)
from pareidolia.templates.composer import PromptComposer
from pareidolia.templates.engine import Jinja2Engine
from pareidolia.templates.loader import TemplateLoader


@pytest.fixture
def mock_loader():
    """Create a mock template loader."""
    loader = Mock(spec=TemplateLoader)
    return loader


@pytest.fixture
def sample_persona():
    """Create a sample persona."""
    return Persona(name="researcher", content="You are an expert researcher.")


@pytest.fixture
def sample_action():
    """Create a sample action template."""
    template = "Task: Research\n{{ persona }}\nTool: {{ tool }}\nLibrary: {{ library }}"
    return Action(name="research", template=template, persona_name="researcher")


@pytest.fixture
def sample_action_with_metadata():
    """Create an action template that uses metadata."""
    template = """---
{% if metadata.description %}description: {{ metadata.description }}{% endif %}
{% if metadata.model %}model: {{ metadata.model }}{% endif %}
---

{{ persona }}

Tool: {{ tool }}
Library: {{ library }}"""
    return Action(
        name="research", template=template, persona_name="researcher"
    )


@pytest.fixture
def generate_config():
    """Create a sample GenerateConfig."""
    return GenerateConfig(
        tool="copilot", library="mylib", output_dir=Path("/output")
    )


@pytest.fixture
def generate_config_no_library():
    """Create a GenerateConfig without library."""
    return GenerateConfig(tool="standard", library=None, output_dir=Path("/output"))


@pytest.fixture
def prompt_config_with_metadata():
    """Create a PromptConfig with metadata."""
    return PromptConfig(
        persona="researcher",
        action="research",
        variants=["update"],
        metadata={
            "description": "Research assistant",
            "model": "claude-3.5-sonnet",
            "temperature": 0.7,
        },
    )


@pytest.fixture
def prompt_config_no_metadata():
    """Create a PromptConfig without metadata."""
    return PromptConfig(
        persona="researcher",
        action="research",
        variants=["update"],
    )


class TestPromptComposerInit:
    """Tests for PromptComposer initialization."""

    def test_init_with_generate_config(self, mock_loader, generate_config):
        """Test initialization with GenerateConfig."""
        composer = PromptComposer(mock_loader, generate_config=generate_config)

        assert composer.loader == mock_loader
        assert composer.generate_config == generate_config
        assert isinstance(composer.engine, Jinja2Engine)

    def test_init_without_generate_config(self, mock_loader):
        """Test initialization without GenerateConfig (backward compatibility)."""
        composer = PromptComposer(mock_loader)

        assert composer.loader == mock_loader
        assert composer.generate_config is None
        assert isinstance(composer.engine, Jinja2Engine)

    def test_init_with_custom_engine(self, mock_loader, generate_config):
        """Test initialization with custom template engine."""
        custom_engine = Mock()
        composer = PromptComposer(
            mock_loader, engine=custom_engine, generate_config=generate_config
        )

        assert composer.engine == custom_engine


class TestPromptComposerBuildContext:
    """Tests for PromptComposer._build_context method."""

    def test_build_context_with_generate_config(
        self, mock_loader, generate_config
    ):
        """Test context building with GenerateConfig provided."""
        composer = PromptComposer(mock_loader, generate_config=generate_config)
        persona = Persona(name="test", content="Test persona")

        context = composer._build_context(persona, [])

        assert context["persona"] == "Test persona"
        assert context["tool"] == "copilot"
        assert context["library"] == "mylib"
        assert context["metadata"] == {}

    def test_build_context_without_generate_config(self, mock_loader):
        """Test context building without GenerateConfig (backward compatibility)."""
        composer = PromptComposer(mock_loader)
        persona = Persona(name="test", content="Test persona")

        context = composer._build_context(persona, [])

        assert context["persona"] == "Test persona"
        assert context["tool"] == "standard"
        assert context["library"] is None
        assert context["metadata"] == {}

    def test_build_context_with_prompt_config(
        self, mock_loader, generate_config, prompt_config_with_metadata
    ):
        """Test context building with PromptConfig metadata."""
        composer = PromptComposer(mock_loader, generate_config=generate_config)
        persona = Persona(name="test", content="Test persona")

        context = composer._build_context(
            persona, [], prompt_config=prompt_config_with_metadata
        )

        assert context["metadata"]["description"] == "Research assistant"
        assert context["metadata"]["model"] == "claude-3.5-sonnet"
        assert context["metadata"]["temperature"] == 0.7

    def test_build_context_without_prompt_config(
        self, mock_loader, generate_config
    ):
        """Test context building without PromptConfig."""
        composer = PromptComposer(mock_loader, generate_config=generate_config)
        persona = Persona(name="test", content="Test persona")

        context = composer._build_context(persona, [])

        assert context["metadata"] == {}

    def test_build_context_with_empty_metadata(
        self, mock_loader, generate_config, prompt_config_no_metadata
    ):
        """Test context building with PromptConfig that has empty metadata."""
        composer = PromptComposer(mock_loader, generate_config=generate_config)
        persona = Persona(name="test", content="Test persona")

        context = composer._build_context(
            persona, [], prompt_config=prompt_config_no_metadata
        )

        assert context["metadata"] == {}

    def test_build_context_with_examples(self, mock_loader, generate_config):
        """Test context building with examples."""
        composer = PromptComposer(mock_loader, generate_config=generate_config)
        persona = Persona(name="test", content="Test persona")
        examples = [
            Example(name="ex1", content="Example 1", is_template=False),
            Example(name="ex2", content="Example 2", is_template=False),
        ]

        context = composer._build_context(persona, examples)

        assert "examples" in context
        assert len(context["examples"]) == 2
        assert context["examples"][0] == "Example 1"
        assert context["examples"][1] == "Example 2"

    def test_build_context_with_template_examples(
        self, mock_loader, generate_config
    ):
        """Test context building with template examples."""
        composer = PromptComposer(mock_loader, generate_config=generate_config)
        persona = Persona(name="test", content="Test persona")
        examples = [
            Example(
                name="ex1",
                content="Tool is {{ tool }}",
                is_template=True,
            ),
        ]

        context = composer._build_context(persona, examples)

        assert "examples" in context
        assert context["examples"][0] == "Tool is copilot"

    def test_build_context_no_library(
        self, mock_loader, generate_config_no_library
    ):
        """Test context building when library is None."""
        composer = PromptComposer(
            mock_loader, generate_config=generate_config_no_library
        )
        persona = Persona(name="test", content="Test persona")

        context = composer._build_context(persona, [])

        assert context["tool"] == "standard"
        assert context["library"] is None


class TestPromptComposerCompose:
    """Tests for PromptComposer.compose method."""

    def test_compose_with_generate_config(
        self,
        mock_loader,
        sample_persona,
        sample_action,
        generate_config,
    ):
        """Test composing with GenerateConfig."""
        mock_loader.load_persona.return_value = sample_persona
        mock_loader.load_action.return_value = sample_action

        composer = PromptComposer(mock_loader, generate_config=generate_config)
        result = composer.compose("research", "researcher")

        assert "You are an expert researcher." in result
        assert "Tool: copilot" in result
        assert "Library: mylib" in result

    def test_compose_without_generate_config(
        self,
        mock_loader,
        sample_persona,
        sample_action,
    ):
        """Test composing without GenerateConfig (backward compatibility)."""
        mock_loader.load_persona.return_value = sample_persona
        mock_loader.load_action.return_value = sample_action

        composer = PromptComposer(mock_loader)
        result = composer.compose("research", "researcher")

        assert "You are an expert researcher." in result
        assert "Tool: standard" in result
        assert "Library: None" in result

    def test_compose_with_metadata(
        self,
        mock_loader,
        sample_persona,
        sample_action_with_metadata,
        generate_config,
        prompt_config_with_metadata,
    ):
        """Test composing with metadata in context."""
        mock_loader.load_persona.return_value = sample_persona
        mock_loader.load_action.return_value = sample_action_with_metadata

        composer = PromptComposer(mock_loader, generate_config=generate_config)
        result = composer.compose(
            "research",
            "researcher",
            prompt_config=prompt_config_with_metadata,
        )

        assert "description: Research assistant" in result
        assert "model: claude-3.5-sonnet" in result
        assert "You are an expert researcher." in result
        assert "Tool: copilot" in result

    def test_compose_without_metadata(
        self,
        mock_loader,
        sample_persona,
        sample_action_with_metadata,
        generate_config,
    ):
        """Test composing with metadata template but no metadata provided."""
        mock_loader.load_persona.return_value = sample_persona
        mock_loader.load_action.return_value = sample_action_with_metadata

        composer = PromptComposer(mock_loader, generate_config=generate_config)
        result = composer.compose("research", "researcher")

        # Metadata conditionals should not render
        assert "description:" not in result
        assert "model:" not in result
        # But other content should be present
        assert "You are an expert researcher." in result

    def test_compose_with_examples(
        self,
        mock_loader,
        sample_persona,
        sample_action,
        generate_config,
    ):
        """Test composing with examples."""
        mock_loader.load_persona.return_value = sample_persona
        mock_loader.load_action.return_value = sample_action
        mock_loader.load_example.return_value = Example(
            name="ex1", content="Example content", is_template=False
        )

        composer = PromptComposer(mock_loader, generate_config=generate_config)
        result = composer.compose(
            "research", "researcher", example_names=["ex1"]
        )

        assert "You are an expert researcher." in result
        mock_loader.load_example.assert_called_once_with("ex1")

    def test_compose_nested_metadata_access(
        self,
        mock_loader,
        sample_persona,
        generate_config,
    ):
        """Test composing with nested metadata access."""
        template = """{{ metadata.settings.model }}
{{ metadata.settings.params.temp }}"""
        action = Action(name="test", template=template, persona_name="researcher")

        prompt_config = PromptConfig(
            persona="researcher",
            action="test",
            variants=["update"],
            metadata={
                "settings": {
                    "model": "claude-3.5",
                    "params": {"temp": 0.8},
                }
            },
        )

        mock_loader.load_persona.return_value = sample_persona
        mock_loader.load_action.return_value = action

        composer = PromptComposer(mock_loader, generate_config=generate_config)
        result = composer.compose("test", "researcher", prompt_config=prompt_config)

        assert "claude-3.5" in result
        assert "0.8" in result


class TestPromptComposerBackwardCompatibility:
    """Tests for backward compatibility."""

    def test_old_style_usage_still_works(
        self,
        mock_loader,
        sample_persona,
        sample_action,
    ):
        """Test that old-style usage without new parameters still works."""
        mock_loader.load_persona.return_value = sample_persona
        mock_loader.load_action.return_value = sample_action

        # Old-style initialization
        composer = PromptComposer(mock_loader)

        # Old-style compose call
        result = composer.compose("research", "researcher")

        assert "You are an expert researcher." in result
        assert "Tool: standard" in result

    def test_partial_upgrade_works(
        self,
        mock_loader,
        sample_persona,
        sample_action,
        generate_config,
    ):
        """Test partial upgrade (GenerateConfig but no PromptConfig)."""
        mock_loader.load_persona.return_value = sample_persona
        mock_loader.load_action.return_value = sample_action

        composer = PromptComposer(mock_loader, generate_config=generate_config)
        result = composer.compose("research", "researcher")

        # Should have tool/library but empty metadata
        assert "Tool: copilot" in result
        assert "Library: mylib" in result
