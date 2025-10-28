"""Command-line interface for pareidolia."""

import argparse
import sys
from pathlib import Path
from typing import Literal

from pareidolia import __version__
from pareidolia.core.config import PareidoliaConfig
from pareidolia.core.exceptions import ConfigurationError, PareidoliaError
from pareidolia.generators.generator import Generator
from pareidolia.generators.initializer import ProjectInitializer


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for the CLI.

    Returns:
        Configured argument parser
    """
    parser = argparse.ArgumentParser(
        prog="pareidolia",
        description=(
            "Generate collections of AI prompt templates for persona-based agents"
        ),
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    parser.add_argument(
        "--mcp",
        action="store_true",
        help="Run in MCP server mode",
    )

    parser.add_argument(
        "--config",
        type=Path,
        default=Path("pareidolia.toml"),
        help="Path to configuration file (default: pareidolia.toml)",
    )

    parser.add_argument(
        "--config-dir",
        type=Path,
        default=Path.cwd(),
        help="Directory containing .pareidolia.toml (for MCP mode, default: current directory)",
    )

    # Create subparsers for commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Generate command
    generate_parser = subparsers.add_parser(
        "generate",
        help="Generate prompts from templates",
    )

    generate_parser.add_argument(
        "--tool",
        type=str,
        help="Target tool (e.g., 'copilot', 'claude-code', 'standard')",
    )

    generate_parser.add_argument(
        "--library",
        type=str,
        help="Library name for bundled generation",
    )

    generate_parser.add_argument(
        "--output-dir",
        type=str,
        help="Output directory for generated prompts",
    )

    generate_parser.add_argument(
        "--persona",
        type=str,
        help="Persona name to use (defaults to first available)",
    )

    generate_parser.add_argument(
        "--examples",
        type=str,
        nargs="+",
        help="Example names to include",
    )

    generate_parser.add_argument(
        "--action",
        type=str,
        help="Specific action to generate (generates all if not specified)",
    )

    # Init command
    init_parser = subparsers.add_parser(
        "init",
        help="Initialize a new Pareidolia project",
    )

    init_parser.add_argument(
        "directory",
        nargs="?",
        type=str,
        default=".",
        help=(
            "Directory where the project should be initialized "
            "(default: current directory)"
        ),
    )

    init_parser.add_argument(
        "--no-scaffold",
        action="store_true",
        help="Only create configuration file without directory structure and examples",
    )

    return parser


def handle_init(directory: str, no_scaffold: bool) -> int:
    """Handle the init command.

    Creates a new Pareidolia project with configuration file and optionally
    scaffolds the full directory structure with example files.

    Args:
        directory: Directory where the project should be initialized
        no_scaffold: If True, only create config file without directory structure

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        directory_path = Path(directory)

        # Create target directory if it doesn't exist
        if not directory_path.exists():
            try:
                directory_path.mkdir(parents=True, exist_ok=True)
            except PermissionError:
                print(
                    f"Error: Permission denied creating directory {directory_path}",
                    file=sys.stderr,
                )
                return 1
            except OSError as e:
                print(
                    f"Error: Failed to create directory {directory_path}: {e}",
                    file=sys.stderr,
                )
                return 1

        # Initialize the project
        initializer = ProjectInitializer()

        # Create configuration file
        initializer.create_config_file(directory_path)
        print("✓ Created configuration file: .pareidolia.toml")

        # Scaffold full project structure if requested
        if not no_scaffold:
            pareidolia_root = directory_path / "pareidolia"

            initializer.scaffold_directories(pareidolia_root)
            print("✓ Created directory structure")

            initializer.create_example_files(pareidolia_root)
            print("✓ Created example files")

            initializer.create_gitignore(directory_path / "prompts")

        print("\nProject initialized successfully!")
        print("\nNext steps:")
        print("  1. Review the configuration in .pareidolia.toml")
        print("  2. Customize the example files in pareidolia/")
        print("  3. Run 'pareidolia generate' to generate prompts")

        return 0

    except ConfigurationError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


def handle_mcp(config_dir: Path) -> int:
    """Handle MCP server mode.

    Args:
        config_dir: Directory containing .pareidolia.toml

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        from pareidolia.mcp.server import create_server

        # Determine mode - use 'mcp' mode by default
        mode: Literal["cli", "mcp"] = "mcp"

        # Create and run server
        server = create_server(config_dir=config_dir, mode=mode)
        server.run()
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def handle_generate(
    config: PareidoliaConfig,
    persona: str | None,
    examples: list[str] | None,
    action: str | None,
) -> int:
    """Handle the generate command.

    Args:
        config: Pareidolia configuration
        persona: Optional persona name
        examples: Optional list of example names
        action: Optional specific action to generate

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        generator = Generator(config)

        if action:
            # Generate single action
            if not persona:
                print("Error: --persona is required when generating a specific action")
                return 1

            result = generator.generate_action(action, persona, examples)
        else:
            # Generate all actions
            result = generator.generate_all(persona, examples)

        # Display results
        if result.files_generated:
            print(f"Successfully generated {len(result.files_generated)} prompt(s):")
            for path in result.files_generated:
                print(f"  - {path}")

        if result.errors:
            print(f"\nEncountered {len(result.errors)} error(s):")
            for error in result.errors:
                print(f"  - {error}")

        return 0 if result.success else 1

    except PareidoliaError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


def main() -> int:
    """Main entry point for the CLI.

    Returns:
        Exit code
    """
    parser = create_parser()
    args = parser.parse_args()

    # Handle MCP mode
    if args.mcp:
        return handle_mcp(args.config_dir)

    # Show help if no command specified
    if not args.command:
        parser.print_help()
        return 0

    # Handle init command separately (doesn't need config)
    if args.command == "init":
        return handle_init(args.directory, args.no_scaffold)

    # Load configuration for other commands
    try:
        if args.config.exists():
            config = PareidoliaConfig.from_file(args.config)
        else:
            # Use defaults if no config file
            config = PareidoliaConfig.from_defaults()

        # Apply CLI overrides for generate command
        if args.command == "generate":
            config = config.merge_overrides(
                tool=args.tool,
                library=args.library,
                output_dir=args.output_dir,
            )
    except PareidoliaError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        return 1

    # Handle commands
    if args.command == "generate":
        return handle_generate(
            config,
            args.persona,
            args.examples,
            args.action,
        )

    return 0


def cli_main() -> None:
    """Entry point wrapper that calls sys.exit."""
    sys.exit(main())


if __name__ == "__main__":
    cli_main()
