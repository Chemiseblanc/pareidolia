"""Integration tests for MCP server."""

from pathlib import Path
from unittest.mock import patch

import pytest

from pareidolia.mcp.server import create_server


@pytest.fixture
def temp_project(tmp_path: Path) -> Path:
    """Create a temporary Pareidolia project with example files."""
    # Create directory structure
    pareidolia_root = tmp_path / "pareidolia"
    persona_dir = pareidolia_root / "persona"
    action_dir = pareidolia_root / "action"
    example_dir = pareidolia_root / "example"

    persona_dir.mkdir(parents=True)
    action_dir.mkdir(parents=True)
    example_dir.mkdir(parents=True)

    # Create a persona
    (persona_dir / "researcher.md").write_text(
        "You are an expert researcher with deep analytical skills."
    )

    # Create actions for the persona
    (action_dir / "research.md.j2").write_text(
        """{{ persona }}

Task: Conduct thorough research on the given topic.

Tool: {{ tool }}
Library: {{ library }}
"""
    )

    (action_dir / "analyze.md.j2").write_text(
        """{{ persona }}

Task: Analyze the provided data systematically.
"""
    )

    # Create an example
    (example_dir / "example1.md").write_text(
        """Example research output:

1. Topic overview
2. Key findings
3. Recommendations
"""
    )

    # Create config file
    config_file = tmp_path / ".pareidolia.toml"
    config_file.write_text(
        """
[pareidolia]
root = "pareidolia"

[generate]
tool = "copilot"
output_dir = "prompts"
"""
    )

    return tmp_path


class TestMCPServerIntegration:
    """Integration tests for MCP server end-to-end functionality."""

    def test_server_creation_and_initialization(self, temp_project: Path) -> None:
        """Test creating and initializing MCP server with real project."""
        server = create_server(config_dir=temp_project, mode="cli")

        assert server is not None
        assert server.config.config_dir == temp_project
        assert server.pareidolia_config.root == temp_project / "pareidolia"
        assert server.generator is not None

    def test_server_loads_project_structure(self, temp_project: Path) -> None:
        """Test that server correctly loads project structure."""
        server = create_server(config_dir=temp_project, mode="cli")

        # Verify personas are loaded
        persona_names = server.generator.loader.list_personas()
        assert len(persona_names) == 1
        assert "researcher" in persona_names

        # Verify actions are loaded
        action_names = server.generator.loader.list_actions()
        assert len(action_names) == 2
        assert "research" in action_names
        assert "analyze" in action_names

        # Verify examples are loaded
        example_names = server.generator.loader.list_examples()
        assert len(example_names) == 1
        assert "example1" in example_names

    @patch("pareidolia.mcp.server.FastMCP")
    def test_server_registers_tools(
        self, mock_fastmcp_class, temp_project: Path
    ) -> None:
        """Test that server registers all MCP tools on initialization."""
        from unittest.mock import Mock

        mock_mcp = Mock()
        mock_fastmcp_class.return_value = mock_mcp

        # Track tool registrations
        registered_tools = []

        def tool_decorator():
            def decorator(func):
                registered_tools.append(func.__name__)
                return func

            return decorator

        mock_mcp.tool = tool_decorator

        create_server(config_dir=temp_project, mode="cli")

        # Verify all expected tools were registered
        assert "list_personas" in registered_tools
        assert "list_actions" in registered_tools
        assert "list_examples" in registered_tools
        assert "generate_prompt" in registered_tools
        assert "generate_with_sampler" in registered_tools
        assert "generate_variants" in registered_tools
        assert "compose_prompt" in registered_tools

    def test_server_with_missing_config_uses_defaults(self, tmp_path: Path) -> None:
        """Test server uses defaults when config file is missing."""
        # Create minimal structure without config file
        pareidolia_root = tmp_path / "pareidolia"
        (pareidolia_root / "persona").mkdir(parents=True)
        (pareidolia_root / "action").mkdir(parents=True)
        (pareidolia_root / "example").mkdir(parents=True)

        server = create_server(config_dir=tmp_path, mode="cli")

        assert server.pareidolia_config.generate.tool == "standard"
        assert server.pareidolia_config.root == tmp_path / "pareidolia"

    def test_server_modes(self, temp_project: Path) -> None:
        """Test server can be created in different modes."""
        # CLI mode
        cli_server = create_server(config_dir=temp_project, mode="cli")
        assert cli_server.config.mode == "cli"

        # MCP mode
        mcp_server = create_server(config_dir=temp_project, mode="mcp")
        assert mcp_server.config.mode == "mcp"


class TestMCPToolsIntegration:
    """Integration tests for MCP tools with real project data."""

    def test_list_personas_with_real_data(self, temp_project: Path) -> None:
        """Test list_personas tool with real project data."""
        server = create_server(config_dir=temp_project, mode="cli")

        # Access the loader to get persona names
        persona_names = server.generator.loader.list_personas()

        assert len(persona_names) == 1
        assert "researcher" in persona_names

        # Load the actual persona to verify content
        persona = server.generator.loader.load_persona("researcher")
        assert "expert researcher" in persona.content.lower()

    def test_list_actions_with_real_data(self, temp_project: Path) -> None:
        """Test list_actions tool with real project data."""
        server = create_server(config_dir=temp_project, mode="cli")

        action_names = server.generator.loader.list_actions()

        assert len(action_names) == 2
        assert "research" in action_names
        assert "analyze" in action_names

    def test_generate_prompt_with_real_data(self, temp_project: Path) -> None:
        """Test generate_prompt with real project data."""
        server = create_server(config_dir=temp_project, mode="cli")

        # Generate a prompt
        prompt = server.generator.composer.compose(
            action_name="research",
            persona_name="researcher",
        )

        assert "expert researcher" in prompt.lower()
        assert "conduct thorough research" in prompt.lower()
        assert "copilot" in prompt.lower()  # From config

    def test_generate_prompt_with_examples(self, temp_project: Path) -> None:
        """Test generate_prompt with examples included."""
        server = create_server(config_dir=temp_project, mode="cli")

        # Generate with examples
        prompt = server.generator.composer.compose(
            action_name="research",
            persona_name="researcher",
            example_names=["example1"],
        )

        assert "expert researcher" in prompt.lower()
        assert "conduct thorough research" in prompt.lower()
