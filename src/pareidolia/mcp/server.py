"""MCP server implementation for Pareidolia."""

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from fastmcp import FastMCP

from pareidolia.core.config import PareidoliaConfig
from pareidolia.generators.generator import Generator
from pareidolia.mcp.tools import register_tools


@dataclass(frozen=True)
class MCPServerConfig:
    """Configuration for MCP server.

    Attributes:
        config_dir: Directory containing Pareidolia configuration
        mode: Server mode - 'cli' for testing, 'mcp' for MCP protocol
    """

    config_dir: Path
    mode: Literal["cli", "mcp"] = "cli"


class PareidoliaMCPServer:
    """FastMCP server for exposing Pareidolia prompts.

    This server provides MCP tools for listing, generating, and composing
    prompts using the Pareidolia template system.

    Attributes:
        config: MCP server configuration
        pareidolia_config: Loaded Pareidolia configuration
        mcp: FastMCP server instance
        generator: Prompt generator instance
    """

    def __init__(self, config: MCPServerConfig) -> None:
        """Initialize MCP server with configuration.

        Args:
            config: MCP server configuration

        Raises:
            ConfigurationError: If configuration cannot be loaded
        """
        self.config = config
        self.pareidolia_config = self._load_pareidolia_config()

        # Initialize FastMCP server
        self.mcp = FastMCP("pareidolia-prompts")

        # Initialize generator
        self.generator = Generator(self.pareidolia_config)

        # Register MCP tools
        register_tools(self.mcp, self.generator, self.pareidolia_config)

    def _load_pareidolia_config(self) -> PareidoliaConfig:
        """Load Pareidolia configuration from the config directory.

        Returns:
            Loaded Pareidolia configuration

        Raises:
            ConfigurationError: If configuration cannot be loaded
        """
        config_file = self.config.config_dir / ".pareidolia.toml"

        if config_file.exists():
            return PareidoliaConfig.from_file(config_file)
        else:
            # Use defaults with specified root
            return PareidoliaConfig.from_defaults(
                project_root=self.config.config_dir
            )

    def run(self) -> None:
        """Run the MCP server in the configured mode.

        In CLI mode, runs with stdio transport for testing.
        In MCP mode, runs as an MCP server.

        Raises:
            RuntimeError: If server fails to start
        """
        try:
            if self.config.mode == "cli":
                # CLI mode for testing and debugging
                print("Running in CLI mode (stdio transport)", file=sys.stderr)
                self.mcp.run(transport="stdio")
            else:
                # MCP mode
                print("Running in MCP mode", file=sys.stderr)
                self.mcp.run()
        except Exception as e:
            raise RuntimeError(f"Server failed to start: {e}") from e


def create_server(
    config_dir: Path | None = None,
    mode: Literal["cli", "mcp"] = "cli",
) -> PareidoliaMCPServer:
    """Create an MCP server instance.

    Args:
        config_dir: Directory containing Pareidolia configuration.
                   Defaults to current directory.
        mode: Server mode ('cli' or 'mcp')

    Returns:
        Initialized MCP server

    Raises:
        ConfigurationError: If configuration cannot be loaded
    """
    if config_dir is None:
        config_dir = Path.cwd()

    server_config = MCPServerConfig(config_dir=config_dir, mode=mode)
    return PareidoliaMCPServer(server_config)
