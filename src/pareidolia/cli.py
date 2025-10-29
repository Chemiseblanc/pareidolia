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
from pareidolia.generators.variant_cache import VariantCache
from pareidolia.generators.variant_saver import VariantSaver


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
        help=(
            "Directory containing .pareidolia.toml "
            "(for MCP mode, default: current directory)"
        ),
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

    # Save command
    save_parser = subparsers.add_parser(
        "save",
        help="Save cached variants as action templates",
    )

    save_parser.add_argument(
        "--variant",
        nargs="+",
        type=str,
        help="Filter by variant name(s)",
    )

    save_parser.add_argument(
        "--action",
        type=str,
        help="Filter by action name",
    )

    save_parser.add_argument(
        "--list",
        action="store_true",
        help="List cached variants without saving",
    )

    save_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing files",
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

        # Check if variants were cached
        cache = VariantCache()
        if cache.has_variants():
            count = cache.count()
            print(
                f"\n{count} variant(s) cached. "
                "Use 'pareidolia save' to persist them as templates."
            )

        return 0 if result.success else 1

    except PareidoliaError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


def handle_save(
    config: PareidoliaConfig,
    variant_names: list[str] | None,
    action_name: str | None,
    list_only: bool,
    force: bool,
) -> int:
    """Handle the save command.

    Args:
        config: Pareidolia configuration
        variant_names: Optional list of variant names to filter by
        action_name: Optional action name to filter by
        list_only: If True, only list cached variants without saving
        force: If True, overwrite existing files

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        # Get all cached variants
        cache = VariantCache()
        cached_variants = cache.get_all()

        if not cached_variants:
            print("No cached variants found.")
            print("Generate variants first using 'pareidolia generate'.")
            return 1

        # Apply filters
        filtered_variants = cached_variants

        if variant_names:
            filtered_variants = [
                v for v in filtered_variants if v.variant_name in variant_names
            ]

        if action_name:
            filtered_variants = [
                v for v in filtered_variants if v.action_name == action_name
            ]

        if not filtered_variants:
            print("No cached variants match the specified filters.")
            return 1

        # List only mode
        if list_only:
            print("Cached Variants:")
            print(
                f"  {'Variant':<15} {'Action':<15} {'Persona':<15} {'Generated':<20}"
            )
            print(
                f"  {'-' * 15} {'-' * 15} {'-' * 15} {'-' * 20}"
            )
            for variant in filtered_variants:
                timestamp = variant.generated_at.strftime("%Y-%m-%d %H:%M:%S")
                print(
                    f"  {variant.variant_name:<15} "
                    f"{variant.action_name:<15} "
                    f"{variant.persona_name:<15} "
                    f"{timestamp:<20}"
                )
            return 0

        # Save variants
        saver = VariantSaver(config.root.parent)
        results = saver.save_all(filtered_variants, force=force)

        # Categorize results
        saved = []
        skipped = []
        errors = []

        for path, (was_saved, error_msg) in results.items():
            if was_saved:
                saved.append(path)
            elif error_msg == "File exists":
                # File exists is a skip, not an error
                skipped.append(path)
            elif error_msg:
                # Other error messages are real errors
                errors.append((path, error_msg))
            else:
                # was_saved=False, no error_msg - shouldn't happen but treat as skip
                skipped.append(path)

        # Display results
        if saved:
            print(f"Successfully saved {len(saved)} template(s):")
            for path in saved:
                print(f"  ✓ {path}")

        if skipped:
            print(
                f"\nSkipped {len(skipped)} existing file(s) "
                "(use --force to overwrite):"
            )
            for path in skipped:
                print(f"  - {path}")

        if errors:
            print(f"\nFailed to save {len(errors)} template(s):")
            for path, error_msg in errors:
                print(f"  ✗ {path}: {error_msg}")

        # Return 0 if there were saves or skips (no errors), 1 if any errors
        return 0 if not errors else 1

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

    if args.command == "save":
        return handle_save(
            config,
            args.variant,
            args.action,
            args.list,
            args.force,
        )

    return 0


def cli_main() -> None:
    """Entry point wrapper that calls sys.exit."""
    sys.exit(main())


if __name__ == "__main__":
    cli_main()
