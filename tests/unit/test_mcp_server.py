"""Unit tests for MCP server."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from pareidolia.mcp.server import MCPServerConfig, PareidoliaMCPServer, create_server


class TestMCPServerConfig:
    """Tests for MCPServerConfig dataclass."""

    def test_server_config_creation_with_defaults(self, tmp_path: Path) -> None:
        """Test server config creation with default values."""
        config = MCPServerConfig(config_dir=tmp_path)

        assert config.config_dir == tmp_path
        assert config.mode == "cli"

    def test_server_config_creation_with_mcp_mode(self, tmp_path: Path) -> None:
        """Test server config creation with MCP mode."""
        config = MCPServerConfig(config_dir=tmp_path, mode="mcp")

        assert config.config_dir == tmp_path
        assert config.mode == "mcp"

    def test_server_config_is_frozen(self, tmp_path: Path) -> None:
        """Test that server config is immutable."""
        config = MCPServerConfig(config_dir=tmp_path)

        with pytest.raises(AttributeError):
            config.mode = "mcp"  # type: ignore


class TestPareidoliaMCPServer:
    """Tests for PareidoliaMCPServer."""

    def test_server_initialization_loads_config_from_file(
        self, tmp_path: Path
    ) -> None:
        """Test that server loads Pareidolia config from file if exists."""
        # Create a minimal config file
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

        # Create necessary directories
        (tmp_path / "pareidolia" / "persona").mkdir(parents=True)
        (tmp_path / "pareidolia" / "action").mkdir(parents=True)
        (tmp_path / "pareidolia" / "example").mkdir(parents=True)

        server_config = MCPServerConfig(config_dir=tmp_path)
        server = PareidoliaMCPServer(server_config)

        assert server.pareidolia_config.root == tmp_path / "pareidolia"
        assert server.pareidolia_config.generate.tool == "copilot"

    def test_server_initialization_uses_defaults_without_config(
        self, tmp_path: Path
    ) -> None:
        """Test that server uses defaults when no config file exists."""
        # Create necessary directories
        (tmp_path / "pareidolia" / "persona").mkdir(parents=True)
        (tmp_path / "pareidolia" / "action").mkdir(parents=True)
        (tmp_path / "pareidolia" / "example").mkdir(parents=True)

        server_config = MCPServerConfig(config_dir=tmp_path)
        server = PareidoliaMCPServer(server_config)

        assert server.pareidolia_config.root == tmp_path / "pareidolia"
        assert server.pareidolia_config.generate.tool == "standard"

    def test_server_initialization_creates_mcp_instance(self, tmp_path: Path) -> None:
        """Test that server creates FastMCP instance."""
        # Create necessary directories
        (tmp_path / "pareidolia" / "persona").mkdir(parents=True)
        (tmp_path / "pareidolia" / "action").mkdir(parents=True)
        (tmp_path / "pareidolia" / "example").mkdir(parents=True)

        server_config = MCPServerConfig(config_dir=tmp_path)
        server = PareidoliaMCPServer(server_config)

        assert server.mcp is not None
        assert server.mcp.name == "pareidolia-prompts"

    def test_server_initialization_creates_generator(self, tmp_path: Path) -> None:
        """Test that server creates Generator instance."""
        # Create necessary directories
        (tmp_path / "pareidolia" / "persona").mkdir(parents=True)
        (tmp_path / "pareidolia" / "action").mkdir(parents=True)
        (tmp_path / "pareidolia" / "example").mkdir(parents=True)

        server_config = MCPServerConfig(config_dir=tmp_path)
        server = PareidoliaMCPServer(server_config)

        assert server.generator is not None

    @patch("pareidolia.mcp.server.FastMCP")
    def test_server_run_in_cli_mode(
        self, mock_fastmcp_class: Mock, tmp_path: Path
    ) -> None:
        """Test that server runs with stdio transport in CLI mode."""
        # Create necessary directories
        (tmp_path / "pareidolia" / "persona").mkdir(parents=True)
        (tmp_path / "pareidolia" / "action").mkdir(parents=True)
        (tmp_path / "pareidolia" / "example").mkdir(parents=True)

        # Setup mock
        mock_mcp = Mock()
        mock_fastmcp_class.return_value = mock_mcp

        server_config = MCPServerConfig(config_dir=tmp_path, mode="cli")
        server = PareidoliaMCPServer(server_config)
        server.run()

        # Verify run was called with stdio transport
        mock_mcp.run.assert_called_once_with(transport="stdio")

    @patch("pareidolia.mcp.server.FastMCP")
    def test_server_run_in_mcp_mode(
        self, mock_fastmcp_class: Mock, tmp_path: Path
    ) -> None:
        """Test that server runs without args in MCP mode."""
        # Create necessary directories
        (tmp_path / "pareidolia" / "persona").mkdir(parents=True)
        (tmp_path / "pareidolia" / "action").mkdir(parents=True)
        (tmp_path / "pareidolia" / "example").mkdir(parents=True)

        # Setup mock
        mock_mcp = Mock()
        mock_fastmcp_class.return_value = mock_mcp

        server_config = MCPServerConfig(config_dir=tmp_path, mode="mcp")
        server = PareidoliaMCPServer(server_config)
        server.run()

        # Verify run was called without transport arg
        mock_mcp.run.assert_called_once_with()


class TestCreateServer:
    """Tests for create_server factory function."""

    def test_create_server_with_defaults(self, tmp_path: Path) -> None:
        """Test creating server with default parameters."""
        # Create necessary directories
        (tmp_path / "pareidolia" / "persona").mkdir(parents=True)
        (tmp_path / "pareidolia" / "action").mkdir(parents=True)
        (tmp_path / "pareidolia" / "example").mkdir(parents=True)

        with patch("pareidolia.mcp.server.Path.cwd", return_value=tmp_path):
            server = create_server()

        assert server.config.config_dir == tmp_path
        assert server.config.mode == "cli"

    def test_create_server_with_custom_config_dir(self, tmp_path: Path) -> None:
        """Test creating server with custom config directory."""
        # Create necessary directories
        (tmp_path / "pareidolia" / "persona").mkdir(parents=True)
        (tmp_path / "pareidolia" / "action").mkdir(parents=True)
        (tmp_path / "pareidolia" / "example").mkdir(parents=True)

        server = create_server(config_dir=tmp_path, mode="cli")

        assert server.config.config_dir == tmp_path
        assert server.config.mode == "cli"

    def test_create_server_with_mcp_mode(self, tmp_path: Path) -> None:
        """Test creating server in MCP mode."""
        # Create necessary directories
        (tmp_path / "pareidolia" / "persona").mkdir(parents=True)
        (tmp_path / "pareidolia" / "action").mkdir(parents=True)
        (tmp_path / "pareidolia" / "example").mkdir(parents=True)

        server = create_server(config_dir=tmp_path, mode="mcp")

        assert server.config.mode == "mcp"
