"""Command-line interface for pareidolia."""

import argparse
import sys
from pathlib import Path

from pareidolia import __version__
from pareidolia.core.config import PareidoliaConfig
from pareidolia.core.exceptions import PareidoliaError
from pareidolia.generators.exporter import Exporter


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
        "--config",
        type=Path,
        default=Path("pareidolia.toml"),
        help="Path to configuration file (default: pareidolia.toml)",
    )

    # Create subparsers for commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Export command
    export_parser = subparsers.add_parser(
        "export",
        help="Export prompts to files",
    )

    export_parser.add_argument(
        "--tool",
        type=str,
        help="Target tool (e.g., 'copilot', 'claude-code', 'standard')",
    )

    export_parser.add_argument(
        "--library",
        type=str,
        help="Library name for bundled exports",
    )

    export_parser.add_argument(
        "--output-dir",
        type=str,
        help="Output directory for generated prompts",
    )

    export_parser.add_argument(
        "--persona",
        type=str,
        help="Persona name to use (defaults to first available)",
    )

    export_parser.add_argument(
        "--examples",
        type=str,
        nargs="+",
        help="Example names to include",
    )

    export_parser.add_argument(
        "--action",
        type=str,
        help="Specific action to export (exports all if not specified)",
    )

    return parser


def handle_export(
    config: PareidoliaConfig,
    persona: str | None,
    examples: list[str] | None,
    action: str | None,
) -> int:
    """Handle the export command.

    Args:
        config: Pareidolia configuration
        persona: Optional persona name
        examples: Optional list of example names
        action: Optional specific action to export

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        exporter = Exporter(config)

        if action:
            # Export single action
            if not persona:
                print("Error: --persona is required when exporting a specific action")
                return 1

            result = exporter.export_action(action, persona, examples)
        else:
            # Export all actions
            result = exporter.export_all(persona, examples)

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

    # Show help if no command specified
    if not args.command:
        parser.print_help()
        return 0

    # Load configuration
    try:
        if args.config.exists():
            config = PareidoliaConfig.from_file(args.config)
        else:
            # Use defaults if no config file
            config = PareidoliaConfig.from_defaults()

        # Apply CLI overrides for export command
        if args.command == "export":
            config = config.merge_overrides(
                tool=args.tool,
                library=args.library,
                output_dir=args.output_dir,
            )
    except PareidoliaError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        return 1

    # Handle commands
    if args.command == "export":
        return handle_export(
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
