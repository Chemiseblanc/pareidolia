"""CLI tool abstraction for variant generation."""

import shutil
import subprocess
from typing import Protocol

from pareidolia.core.exceptions import CLIToolError


class CLITool(Protocol):
    """Protocol for AI CLI tools used in variant generation."""

    @property
    def name(self) -> str:
        """Return the tool name."""
        ...

    @property
    def command(self) -> str:
        """Return the command name to check for availability."""
        ...

    def is_available(self) -> bool:
        """Check if the tool is available in PATH.

        Returns:
            True if the tool command is found in PATH
        """
        ...

    def generate_variant(
        self,
        variant_prompt: str,
        base_prompt: str,
        timeout: int = 60,
    ) -> str:
        """Generate a variant using the CLI tool.

        Args:
            variant_prompt: Rendered variant template with instructions
            base_prompt: Original prompt content
            timeout: Command timeout in seconds

        Returns:
            Generated variant content

        Raises:
            CLIToolError: If tool invocation fails
        """
        ...


def check_tool_available(command: str) -> bool:
    """Check if a command is available in PATH.

    Args:
        command: Command name to check

    Returns:
        True if command is available
    """
    return shutil.which(command) is not None
