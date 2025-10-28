"""Unit tests for data models."""

from pathlib import Path

import pytest

from pareidolia.core.exceptions import ValidationError
from pareidolia.core.models import (
    Action,
    Example,
    GenerateConfig,
    Persona,
    PromptConfig,
)


class TestPersona:
    """Tests for Persona model."""

    def test_create_valid_persona(self) -> None:
        """Test creating a valid persona."""
        persona = Persona(
            name="researcher",
            content="You are an expert researcher.",
        )
        assert persona.name == "researcher"
        assert persona.content == "You are an expert researcher."

    def test_persona_is_frozen(self) -> None:
        """Test that Persona is immutable."""
        persona = Persona(name="test", content="content")

        with pytest.raises(AttributeError):
            persona.name = "new_name"  # type: ignore

    def test_persona_invalid_name(self) -> None:
        """Test that invalid persona name raises error."""
        with pytest.raises(ValidationError):
            Persona(name="Invalid Name", content="content")

    def test_persona_empty_content(self) -> None:
        """Test that empty content raises error."""
        with pytest.raises(ValueError, match="cannot be empty"):
            Persona(name="test", content="")


class TestAction:
    """Tests for Action model."""

    def test_create_valid_action(self) -> None:
        """Test creating a valid action."""
        action = Action(
            name="research",
            template="{{ persona }}\\n\\nResearch task.",
            persona_name="researcher",
        )
        assert action.name == "research"
        assert "persona" in action.template
        assert action.persona_name == "researcher"

    def test_action_is_frozen(self) -> None:
        """Test that Action is immutable."""
        action = Action(
            name="test",
            template="template",
            persona_name="researcher",
        )

        with pytest.raises(AttributeError):
            action.name = "new_name"  # type: ignore

    def test_action_invalid_name(self) -> None:
        """Test that invalid action name raises error."""
        with pytest.raises(ValidationError):
            Action(
                name="Invalid Name",
                template="template",
                persona_name="researcher",
            )

    def test_action_invalid_persona_name(self) -> None:
        """Test that invalid persona name raises error."""
        with pytest.raises(ValidationError):
            Action(
                name="test",
                template="template",
                persona_name="Invalid Name",
            )

    def test_action_empty_template(self) -> None:
        """Test that empty template raises error."""
        with pytest.raises(ValueError, match="cannot be empty"):
            Action(
                name="test",
                template="",
                persona_name="researcher",
            )


class TestExample:
    """Tests for Example model."""

    def test_create_valid_example(self) -> None:
        """Test creating a valid example."""
        example = Example(
            name="report",
            content="# Report\\n\\nContent here.",
        )
        assert example.name == "report"
        assert example.content.startswith("# Report")
        assert not example.is_template

    def test_create_template_example(self) -> None:
        """Test creating an example that is a template."""
        example = Example(
            name="report",
            content="# {{ title }}",
            is_template=True,
        )
        assert example.is_template

    def test_example_is_frozen(self) -> None:
        """Test that Example is immutable."""
        example = Example(name="test", content="content")

        with pytest.raises(AttributeError):
            example.name = "new_name"  # type: ignore

    def test_example_invalid_name(self) -> None:
        """Test that invalid example name raises error."""
        with pytest.raises(ValidationError):
            Example(name="Invalid Name", content="content")

    def test_example_empty_content(self) -> None:
        """Test that empty content raises error."""
        with pytest.raises(ValueError, match="cannot be empty"):
            Example(name="test", content="")


class TestGenerateConfig:
    """Tests for GenerateConfig model."""

    def test_create_valid_config(self) -> None:
        """Test creating a valid generate config."""
        config = GenerateConfig(
            tool="copilot",
            library="mylib",
            output_dir=Path("output"),
        )
        assert config.tool == "copilot"
        assert config.library == "mylib"
        assert config.output_dir == Path("output")

    def test_create_config_without_library(self) -> None:
        """Test creating config without library."""
        config = GenerateConfig(
            tool="standard",
            library=None,
            output_dir=Path("output"),
        )
        assert config.library is None

    def test_config_is_frozen(self) -> None:
        """Test that GenerateConfig is immutable."""
        config = GenerateConfig(
            tool="standard",
            library=None,
            output_dir=Path("output"),
        )

        with pytest.raises(AttributeError):
            config.tool = "copilot"  # type: ignore

    def test_config_empty_tool(self) -> None:
        """Test that empty tool raises error."""
        with pytest.raises(ValueError, match="Tool cannot be empty"):
            GenerateConfig(tool="", library=None, output_dir=Path("output"))

    def test_config_invalid_library(self) -> None:
        """Test that invalid library name raises error."""
        with pytest.raises(ValidationError):
            GenerateConfig(
                tool="standard",
                library="Invalid Library",
                output_dir=Path("output"),
            )


class TestPromptConfig:
    """Tests for PromptConfig model."""

    def test_prompt_config_creation_with_valid_data(self) -> None:
        """Test creating a valid prompt config."""
        config = PromptConfig(
            persona="researcher",
            action="research",
            variants=["update", "refine", "summarize"],
        )
        assert config.persona == "researcher"
        assert config.action == "research"
        assert config.variants == ["update", "refine", "summarize"]
        assert config.cli_tool is None

    def test_prompt_config_with_cli_tool(self) -> None:
        """Test creating prompt config with specified CLI tool."""
        config = PromptConfig(
            persona="researcher",
            action="research",
            variants=["update"],
            cli_tool="claude",
        )
        assert config.cli_tool == "claude"

    def test_prompt_config_is_frozen(self) -> None:
        """Test that PromptConfig is immutable."""
        config = PromptConfig(
            persona="researcher",
            action="research",
            variants=["update"],
        )

        with pytest.raises(AttributeError):
            config.persona = "new_persona"  # type: ignore

    def test_prompt_config_validates_persona(self) -> None:
        """Test that invalid persona name raises error."""
        with pytest.raises(ValidationError):
            PromptConfig(
                persona="Invalid Persona",
                action="research",
                variants=["update"],
            )

    def test_prompt_config_validates_action(self) -> None:
        """Test that invalid action name raises error."""
        with pytest.raises(ValidationError):
            PromptConfig(
                persona="researcher",
                action="Invalid Action",
                variants=["update"],
            )

    def test_prompt_config_validates_variants_list(self) -> None:
        """Test that empty variants list raises error."""
        with pytest.raises(ValueError, match="cannot be empty"):
            PromptConfig(
                persona="researcher",
                action="research",
                variants=[],
            )

    def test_prompt_config_validates_variant_names(self) -> None:
        """Test that invalid variant names raise error."""
        with pytest.raises(ValidationError):
            PromptConfig(
                persona="researcher",
                action="research",
                variants=["update", "Invalid Name"],
            )

    def test_prompt_config_accepts_optional_cli_tool(self) -> None:
        """Test that CLI tool is optional."""
        config = PromptConfig(
            persona="researcher",
            action="research",
            variants=["update"],
            cli_tool=None,
        )
        assert config.cli_tool is None

    def test_prompt_config_rejects_empty_cli_tool(self) -> None:
        """Test that empty CLI tool string raises error."""
        with pytest.raises(ValueError, match="cannot be empty string"):
            PromptConfig(
                persona="researcher",
                action="research",
                variants=["update"],
                cli_tool="",
            )

        with pytest.raises(ValueError, match="cannot be empty string"):
            PromptConfig(
                persona="researcher",
                action="research",
                variants=["update"],
                cli_tool="   ",
            )
