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
    persona_dir = pareidolia_root / "personas"
    action_dir = pareidolia_root / "actions"
    example_dir = pareidolia_root / "examples"

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

    # Create config file with prompt configurations
    config_file = tmp_path / "pareidolia.toml"
    config_file.write_text(
        """
[pareidolia]
root = "pareidolia"

[generate]
tool = "copilot"
output_dir = "prompts"

[[prompt]]
persona = "researcher"
action = "research"
variants = ["update", "refine"]

[prompt.metadata]
description = "Research prompt"

[[prompt]]
persona = "researcher"
action = "analyze"
variants = ["expand"]

[prompt.metadata]
description = "Analysis prompt"
"""
    )

    return tmp_path


class TestMCPServerIntegration:
    """Integration tests for MCP server end-to-end functionality."""

    def test_server_creation_and_initialization(self, temp_project: Path) -> None:
        """Test creating and initializing MCP server with real project."""
        server = create_server(source_uri=str(temp_project))

        assert server is not None
        assert server.config.source_uri == str(temp_project)
        assert server.pareidolia_config.root == temp_project / "pareidolia"
        assert server.generator is not None

    def test_server_loads_project_structure(self, temp_project: Path) -> None:
        """Test that server correctly loads project structure."""
        server = create_server(source_uri=str(temp_project))

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
    def test_server_registers_prompts(
        self, mock_fastmcp_class, temp_project: Path
    ) -> None:
        """Test that server registers all MCP prompts on initialization."""
        from unittest.mock import Mock

        mock_mcp = Mock()
        mock_fastmcp_class.return_value = mock_mcp

        # Track prompt registrations
        registered_prompts = []

        def prompt_decorator():
            def decorator(func):
                registered_prompts.append(func.__name__)
                return func

            return decorator

        mock_mcp.prompt = prompt_decorator

        create_server(source_uri=str(temp_project))

        # Verify expected prompts were registered based on config
        # Config has 2 [[prompt]] blocks:
        # 1. research with variants: update, refine
        #    -> 3 prompts (research, update_research, refine_research)
        # 2. analyze with variants: expand
        #    -> 2 prompts (analyze, expand_analyze)
        # Total: 5 prompts

        assert "research" in registered_prompts
        assert "update_research" in registered_prompts
        assert "refine_research" in registered_prompts
        assert "analyze" in registered_prompts
        assert "expand_analyze" in registered_prompts

        # Should have exactly 5 prompts
        assert len(registered_prompts) == 5

    def test_server_with_missing_config_uses_defaults(self, tmp_path: Path) -> None:
        """Test server uses defaults when config file is missing."""
        # Create minimal structure without config file
        pareidolia_root = tmp_path / "pareidolia"
        (pareidolia_root / "personas").mkdir(parents=True)
        (pareidolia_root / "actions").mkdir(parents=True)
        (pareidolia_root / "examples").mkdir(parents=True)

        server = create_server(source_uri=str(tmp_path))

        assert server.pareidolia_config.generate.tool == "standard"
        assert server.pareidolia_config.root == tmp_path / "pareidolia"

    def test_server_modes(self, temp_project: Path) -> None:
        """Test server is created in MCP mode by default."""
        # create_server always uses MCP mode
        server = create_server(source_uri=str(temp_project))
        assert server.config.mode == "mcp"

    @patch("pareidolia.mcp.server.FastMCP")
    def test_server_with_no_prompts_configured(
        self, mock_fastmcp_class, tmp_path: Path
    ) -> None:
        """Test server handles missing [[prompt]] configs gracefully."""
        from unittest.mock import Mock

        # Create minimal structure without prompt configs
        pareidolia_root = tmp_path / "pareidolia"
        (pareidolia_root / "personas").mkdir(parents=True)
        (pareidolia_root / "actions").mkdir(parents=True)

        # Create config without any [[prompt]] blocks
        config_file = tmp_path / "pareidolia.toml"
        config_file.write_text(
            """
[pareidolia]
root = "pareidolia"

[generate]
tool = "copilot"
output_dir = "prompts"
"""
        )

        mock_mcp = Mock()
        mock_fastmcp_class.return_value = mock_mcp

        # Track prompt registrations
        registered_prompts = []

        def prompt_decorator():
            def decorator(func):
                registered_prompts.append(func.__name__)
                return func

            return decorator

        mock_mcp.prompt = prompt_decorator

        # Server should initialize without error
        server = create_server(source_uri=str(tmp_path))

        # No prompts should be registered
        assert len(registered_prompts) == 0
        assert server is not None


class TestMCPPromptsIntegration:
    """Integration tests for MCP prompts with real project data."""

    def test_prompt_discovery_with_real_config(self, temp_project: Path) -> None:
        """Test that prompts are discovered from real config file."""
        server = create_server(source_uri=str(temp_project))

        # Verify config has prompts
        assert len(server.pareidolia_config.prompt) == 2

        # Check first prompt config
        research_prompt = server.pareidolia_config.prompt[0]
        assert research_prompt.persona == "researcher"
        assert research_prompt.action == "research"
        assert "update" in research_prompt.variants
        assert "refine" in research_prompt.variants

        # Check second prompt config
        analyze_prompt = server.pareidolia_config.prompt[1]
        assert analyze_prompt.persona == "researcher"
        assert analyze_prompt.action == "analyze"
        assert "expand" in analyze_prompt.variants

    def test_base_prompt_generation_with_real_data(self, temp_project: Path) -> None:
        """Test base prompt generation with real project data."""
        server = create_server(source_uri=str(temp_project))

        # Access the loader to verify personas and actions exist
        persona_names = server.generator.loader.list_personas()
        assert "researcher" in persona_names

        action_names = server.generator.loader.list_actions()
        assert "research" in action_names
        assert "analyze" in action_names

        # Generate a prompt directly through composer
        prompt = server.generator.composer.compose(
            action_name="research",
            persona_name="researcher",
        )

        assert "expert researcher" in prompt.lower()
        assert "conduct thorough research" in prompt.lower()
        assert "copilot" in prompt.lower()  # From config

    def test_prompt_metadata_from_config(self, temp_project: Path) -> None:
        """Test that prompt metadata is loaded from config."""
        server = create_server(source_uri=str(temp_project))

        # Check metadata from prompt configs
        research_prompt = server.pareidolia_config.prompt[0]
        assert research_prompt.metadata.get("description") == "Research prompt"

        analyze_prompt = server.pareidolia_config.prompt[1]
        assert analyze_prompt.metadata.get("description") == "Analysis prompt"

