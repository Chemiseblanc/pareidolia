"""Unit tests for MCP tools."""

from pathlib import Path
from unittest.mock import Mock

import pytest

from pareidolia.core.exceptions import ActionNotFoundError, PersonaNotFoundError
from pareidolia.core.models import Action, Example, Persona
from pareidolia.generators.generator import Generator
from pareidolia.mcp.tools import register_tools


class TestMCPTools:
    """Tests for MCP tools registration and functionality."""

    @pytest.fixture
    def mock_mcp(self) -> Mock:
        """Create a mock FastMCP instance."""
        mcp = Mock()
        # Store registered tools
        mcp.registered_tools = {}

        def tool_decorator():
            def decorator(func):
                mcp.registered_tools[func.__name__] = func
                return func

            return decorator

        mcp.tool = tool_decorator
        return mcp

    @pytest.fixture
    def mock_generator(self) -> Mock:
        """Create a mock Generator instance."""
        generator = Mock(spec=Generator)
        generator.loader = Mock()
        generator.composer = Mock()
        generator.variant_generator = Mock()
        return generator

    @pytest.fixture
    def mock_config(self, tmp_path: Path) -> Mock:
        """Create a mock PareidoliaConfig."""
        config = Mock()
        config.root = tmp_path / "pareidolia"
        return config

    def test_register_tools_creates_all_tools(
        self,
        mock_mcp: Mock,
        mock_generator: Mock,
        mock_config: Mock,
    ) -> None:
        """Test that all tools are registered."""
        register_tools(mock_mcp, mock_generator, mock_config)

        assert "list_personas" in mock_mcp.registered_tools
        assert "list_actions" in mock_mcp.registered_tools
        assert "list_examples" in mock_mcp.registered_tools
        assert "generate_prompt" in mock_mcp.registered_tools
        assert "generate_with_sampler" in mock_mcp.registered_tools
        assert "generate_variants" in mock_mcp.registered_tools
        assert "compose_prompt" in mock_mcp.registered_tools

    def test_list_personas_returns_persona_data(
        self,
        mock_mcp: Mock,
        mock_generator: Mock,
        mock_config: Mock,
    ) -> None:
        """Test list_personas tool returns persona information."""
        # Setup mock to return names first, then personas when loaded
        mock_generator.loader.list_personas.return_value = ["researcher", "developer"]
        mock_generator.loader.load_persona.side_effect = [
            Persona(name="researcher", content="Expert researcher persona"),
            Persona(name="developer", content="Expert developer persona"),
        ]

        register_tools(mock_mcp, mock_generator, mock_config)
        list_personas = mock_mcp.registered_tools["list_personas"]

        result = list_personas()

        assert len(result) == 2
        assert result[0]["name"] == "researcher"
        assert "Expert researcher" in result[0]["content_preview"]
        assert result[1]["name"] == "developer"

    def test_list_personas_truncates_long_content(
        self,
        mock_mcp: Mock,
        mock_generator: Mock,
        mock_config: Mock,
    ) -> None:
        """Test list_personas truncates long content with ellipsis."""
        long_content = "x" * 300
        mock_generator.loader.list_personas.return_value = ["test"]
        mock_generator.loader.load_persona.return_value = Persona(
            name="test", content=long_content
        )

        register_tools(mock_mcp, mock_generator, mock_config)
        list_personas = mock_mcp.registered_tools["list_personas"]

        result = list_personas()

        assert len(result[0]["content_preview"]) == 203  # 200 chars + "..."
        assert result[0]["content_preview"].endswith("...")

    def test_list_actions_returns_action_data(
        self,
        mock_mcp: Mock,
        mock_generator: Mock,
        mock_config: Mock,
    ) -> None:
        """Test list_actions tool returns action information."""
        mock_generator.loader.load_persona.return_value = Persona(
            name="researcher", content="Researcher"
        )
        mock_generator.loader.list_actions.return_value = ["research", "analyze"]
        mock_generator.loader.load_action.side_effect = [
            Action(
                name="research",
                template="Research template",
                persona_name="researcher",
            ),
            Action(
                name="analyze",
                template="Analyze template",
                persona_name="researcher",
            ),
        ]

        register_tools(mock_mcp, mock_generator, mock_config)
        list_actions = mock_mcp.registered_tools["list_actions"]

        result = list_actions("researcher")

        assert len(result) == 2
        assert result[0]["name"] == "research"
        assert "Research template" in result[0]["template_preview"]

    def test_list_actions_raises_on_persona_not_found(
        self,
        mock_mcp: Mock,
        mock_generator: Mock,
        mock_config: Mock,
    ) -> None:
        """Test list_actions raises ValueError when persona not found."""
        mock_generator.loader.load_persona.side_effect = PersonaNotFoundError(
            "Persona not found"
        )

        register_tools(mock_mcp, mock_generator, mock_config)
        list_actions = mock_mcp.registered_tools["list_actions"]

        with pytest.raises(ValueError, match="Persona not found"):
            list_actions("nonexistent")

    def test_list_examples_returns_example_data(
        self,
        mock_mcp: Mock,
        mock_generator: Mock,
        mock_config: Mock,
    ) -> None:
        """Test list_examples tool returns example information."""
        mock_generator.loader.list_examples.return_value = ["ex1", "ex2"]
        mock_generator.loader.load_example.side_effect = [
            Example(name="ex1", content="Example 1", is_template=False),
            Example(name="ex2", content="Example 2 {{ var }}", is_template=True),
        ]

        register_tools(mock_mcp, mock_generator, mock_config)
        list_examples = mock_mcp.registered_tools["list_examples"]

        result = list_examples()

        assert len(result) == 2
        assert result[0]["name"] == "ex1"
        assert result[0]["is_template"] == "False"
        assert result[1]["is_template"] == "True"

    def test_generate_prompt_returns_composed_prompt(
        self,
        mock_mcp: Mock,
        mock_generator: Mock,
        mock_config: Mock,
    ) -> None:
        """Test generate_prompt tool returns composed prompt."""
        mock_generator.composer.compose.return_value = "Composed prompt content"

        register_tools(mock_mcp, mock_generator, mock_config)
        generate_prompt = mock_mcp.registered_tools["generate_prompt"]

        result = generate_prompt("research", "researcher")

        assert result == "Composed prompt content"
        mock_generator.composer.compose.assert_called_once()

    def test_generate_prompt_with_examples_and_metadata(
        self,
        mock_mcp: Mock,
        mock_generator: Mock,
        mock_config: Mock,
    ) -> None:
        """Test generate_prompt with examples and metadata."""
        mock_generator.composer.compose.return_value = "Composed prompt"

        register_tools(mock_mcp, mock_generator, mock_config)
        generate_prompt = mock_mcp.registered_tools["generate_prompt"]

        result = generate_prompt(
            "research",
            "researcher",
            examples=["ex1", "ex2"],
            metadata={"description": "Test prompt"},
        )

        assert result == "Composed prompt"
        # Verify compose was called with correct args
        call_args = mock_generator.composer.compose.call_args
        assert call_args[1]["action_name"] == "research"
        assert call_args[1]["persona_name"] == "researcher"
        assert call_args[1]["example_names"] == ["ex1", "ex2"]

    def test_generate_prompt_raises_on_persona_not_found(
        self,
        mock_mcp: Mock,
        mock_generator: Mock,
        mock_config: Mock,
    ) -> None:
        """Test generate_prompt raises ValueError when persona not found."""
        mock_generator.composer.compose.side_effect = PersonaNotFoundError(
            "Persona not found"
        )

        register_tools(mock_mcp, mock_generator, mock_config)
        generate_prompt = mock_mcp.registered_tools["generate_prompt"]

        with pytest.raises(ValueError, match="Persona not found"):
            generate_prompt("research", "nonexistent")

    def test_generate_prompt_raises_on_action_not_found(
        self,
        mock_mcp: Mock,
        mock_generator: Mock,
        mock_config: Mock,
    ) -> None:
        """Test generate_prompt raises ValueError when action not found."""
        mock_generator.composer.compose.side_effect = ActionNotFoundError(
            "Action not found"
        )

        register_tools(mock_mcp, mock_generator, mock_config)
        generate_prompt = mock_mcp.registered_tools["generate_prompt"]

        with pytest.raises(ValueError, match="Action not found"):
            generate_prompt("nonexistent", "researcher")

    def test_generate_with_sampler_returns_prompt(
        self,
        mock_mcp: Mock,
        mock_generator: Mock,
        mock_config: Mock,
    ) -> None:
        """Test generate_with_sampler tool returns prompt."""
        mock_generator.composer.compose.return_value = "Sampler prompt"

        register_tools(mock_mcp, mock_generator, mock_config)
        generate_with_sampler = mock_mcp.registered_tools["generate_with_sampler"]

        result = generate_with_sampler("research", "researcher")

        assert result == "Sampler prompt"

    def test_generate_variants_returns_variant_dict(
        self,
        mock_mcp: Mock,
        mock_generator: Mock,
        mock_config: Mock,
    ) -> None:
        """Test generate_variants returns dictionary of variants."""
        mock_generator.composer.compose.return_value = "Base prompt"
        mock_generator.variant_generator.generate_variants.return_value = {
            "update": "Update variant",
            "refine": "Refine variant",
        }

        register_tools(mock_mcp, mock_generator, mock_config)
        generate_variants = mock_mcp.registered_tools["generate_variants"]

        result = generate_variants(
            "research", "researcher", variants=["update", "refine"]
        )

        assert len(result) == 2
        assert result["update"] == "Update variant"
        assert result["refine"] == "Refine variant"

    def test_generate_variants_raises_on_empty_variants(
        self,
        mock_mcp: Mock,
        mock_generator: Mock,
        mock_config: Mock,
    ) -> None:
        """Test generate_variants raises ValueError on empty variants list."""
        register_tools(mock_mcp, mock_generator, mock_config)
        generate_variants = mock_mcp.registered_tools["generate_variants"]

        with pytest.raises(ValueError, match="Variants list cannot be empty"):
            generate_variants("research", "researcher", variants=[])

    def test_compose_prompt_is_alias_for_generate(
        self,
        mock_mcp: Mock,
        mock_generator: Mock,
        mock_config: Mock,
    ) -> None:
        """Test compose_prompt is an alias for generate_prompt."""
        mock_generator.composer.compose.return_value = "Composed prompt"

        register_tools(mock_mcp, mock_generator, mock_config)
        compose_prompt = mock_mcp.registered_tools["compose_prompt"]

        result = compose_prompt("research", "researcher")

        assert result == "Composed prompt"
        mock_generator.composer.compose.assert_called_once()
