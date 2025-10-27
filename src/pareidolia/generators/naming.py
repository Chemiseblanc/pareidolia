"""Naming convention strategies for different tools."""

from pathlib import Path
from typing import Protocol


class NamingConvention(Protocol):
    """Protocol for naming convention strategies."""

    def get_filename(self, action_name: str, library: str | None = None) -> str:
        """Generate a filename for an action.

        Args:
            action_name: The action name
            library: Optional library name

        Returns:
            The generated filename
        """
        ...

    def get_output_path(
        self,
        output_dir: Path,
        action_name: str,
        library: str | None = None,
    ) -> Path:
        """Generate the full output path for an action.

        Args:
            output_dir: The base output directory
            action_name: The action name
            library: Optional library name

        Returns:
            The complete output path
        """
        ...


class StandardNaming:
    """Standard naming convention: <action>.prompt.md."""

    def get_filename(self, action_name: str, library: str | None = None) -> str:
        """Generate a filename using standard convention.

        Args:
            action_name: The action name
            library: Optional library name (ignored for standard naming)

        Returns:
            Filename in format: <action>.prompt.md
        """
        return f"{action_name}.prompt.md"

    def get_output_path(
        self,
        output_dir: Path,
        action_name: str,
        library: str | None = None,
    ) -> Path:
        """Generate the full output path.

        Args:
            output_dir: The base output directory
            action_name: The action name
            library: Optional library name (ignored)

        Returns:
            Path to output file
        """
        filename = self.get_filename(action_name, library)
        return output_dir / filename


class CopilotNaming:
    """GitHub Copilot library naming: flat with prefix.

    Format: <library>.<action>.prompt.md
    """

    def get_filename(self, action_name: str, library: str | None = None) -> str:
        """Generate a filename using Copilot convention.

        Args:
            action_name: The action name
            library: Optional library name

        Returns:
            Filename in format: <library>.<action>.prompt.md or <action>.prompt.md
        """
        if library:
            return f"{library}.{action_name}.prompt.md"
        return f"{action_name}.prompt.md"

    def get_output_path(
        self,
        output_dir: Path,
        action_name: str,
        library: str | None = None,
    ) -> Path:
        """Generate the full output path.

        Args:
            output_dir: The base output directory
            action_name: The action name
            library: Optional library name

        Returns:
            Path to output file (flat structure)
        """
        filename = self.get_filename(action_name, library)
        return output_dir / filename


class ClaudeCodeNaming:
    """Claude Code library naming: subdirectory structure.

    Format: <library>/<action>.md
    """

    def get_filename(self, action_name: str, library: str | None = None) -> str:
        """Generate a filename using Claude Code convention.

        Args:
            action_name: The action name
            library: Optional library name (used for subdirectory)

        Returns:
            Filename in format: <action>.md
        """
        return f"{action_name}.md"

    def get_output_path(
        self,
        output_dir: Path,
        action_name: str,
        library: str | None = None,
    ) -> Path:
        """Generate the full output path.

        Args:
            output_dir: The base output directory
            action_name: The action name
            library: Optional library name (creates subdirectory)

        Returns:
            Path to output file in subdirectory structure
        """
        filename = self.get_filename(action_name, library)
        if library:
            return output_dir / library / filename
        return output_dir / filename


# Registry of naming conventions
NAMING_CONVENTIONS: dict[str, NamingConvention] = {
    "standard": StandardNaming(),
    "copilot": CopilotNaming(),
    "claude-code": ClaudeCodeNaming(),
}


def get_naming_convention(tool: str) -> NamingConvention:
    """Get the naming convention for a tool.

    Args:
        tool: The tool name

    Returns:
        The naming convention for the tool

    Raises:
        ValueError: If the tool is not recognized
    """
    convention = NAMING_CONVENTIONS.get(tool)
    if convention is None:
        # Default to standard if tool not recognized
        return NAMING_CONVENTIONS["standard"]
    return convention
