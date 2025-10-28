"""CLI entry point for Pareidolia MCP server."""

import sys
from pathlib import Path
from typing import Literal

from pareidolia.mcp.server import create_server


def main() -> int:
    """Main entry point for the MCP server CLI.

    Parses command-line arguments and starts the MCP server.

    Command-line Arguments:
        --mcp: Run in MCP mode (default: CLI mode)
        --config-dir PATH: Path to directory containing .pareidolia.toml
                          (default: current directory)

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    import argparse

    parser = argparse.ArgumentParser(
        prog="pareidolia-mcp",
        description="MCP server for exposing Pareidolia prompts",
    )

    parser.add_argument(
        "--mcp",
        action="store_true",
        help="Run in MCP mode (default: CLI mode for testing)",
    )

    parser.add_argument(
        "--config-dir",
        type=Path,
        default=Path.cwd(),
        help="Directory containing .pareidolia.toml (default: current directory)",
    )

    args = parser.parse_args()

    # Determine mode with proper type
    mode: Literal["cli", "mcp"] = "mcp" if args.mcp else "cli"

    try:
        # Create and run server
        server = create_server(config_dir=args.config_dir, mode=mode)
        server.run()
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
