"""MCP server implementation for Pareidolia."""

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from fastmcp import FastMCP

from pareidolia.core.config import PareidoliaConfig
from pareidolia.mcp.prompts import register_prompts


@dataclass(frozen=True)
class MCPServerConfig:
    """Configuration for MCP server.

    Attributes:
        source_uri: Source URI for prompt templates
        mode: Server mode - 'cli' for testing, 'mcp' for MCP protocol
    """

    source_uri: str
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

        # Load config and initialize generator
        self.pareidolia_config = self._load_pareidolia_config()

        # Initialize FastMCP server
        self.mcp = FastMCP("pareidolia-prompts")

        # Register MCP prompts (generator is set in _load_pareidolia_config)
        register_prompts(self.mcp, self.generator, self.pareidolia_config)

    def _load_pareidolia_config(self) -> PareidoliaConfig:
        """Load Pareidolia configuration from source URI.

        Returns:
            Loaded Pareidolia configuration

        Raises:
            ConfigurationError: If configuration cannot be loaded
        """
        try:
            # Use PareidoliaConfig.from_source() to load config and filesystem
            config, filesystem, template_root = PareidoliaConfig.from_source(
                self.config.source_uri
            )

            # Create TemplateLoader with filesystem
            from pareidolia.templates.loader import TemplateLoader

            loader = TemplateLoader(filesystem, template_root)

            # Create Generator with loader
            from pareidolia.generators.generator import Generator

            self.generator = Generator(config, loader)

            return config

        except Exception as e:
            # Fall back to defaults if config cannot be loaded
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to load config from {self.config.source_uri}: {e}")
            logger.warning("Using default configuration")

            # Parse source_uri to get base path for defaults
            from pathlib import Path

            from pareidolia.utils.filesystem import LocalFileSystem, parse_source_uri

            try:
                fs = parse_source_uri(self.config.source_uri)
                if isinstance(fs, LocalFileSystem):
                    base_path = fs.base_path
                else:
                    base_path = Path.cwd()
            except Exception:
                base_path = Path.cwd()

            # Return default config with appropriate base path
            config = PareidoliaConfig.from_defaults(base_path)

            # Initialize generator with defaults
            from pareidolia.generators.generator import Generator
            self.generator = Generator(config)

            return config

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
    source_uri: str | None = None,
) -> PareidoliaMCPServer:
    """Create an MCP server instance.

    Args:
        source_uri: Source URI for templates (defaults to current directory)

    Returns:
        Initialized MCP server

    Raises:
        ConfigurationError: If configuration cannot be loaded
    """
    if source_uri is None:
        source_uri = str(Path.cwd())

    # Always use 'mcp' mode for production
    server_config = MCPServerConfig(source_uri=source_uri, mode="mcp")
    return PareidoliaMCPServer(server_config)
