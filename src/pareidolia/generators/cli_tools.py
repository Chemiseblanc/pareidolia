"""CLI tool abstraction for variant generation."""

import shutil
import subprocess
from abc import ABC, abstractmethod
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


class BaseCLITool(ABC):
    """Abstract base class for AI CLI tool implementations.
    
    This class provides common subprocess execution logic and error handling
    for AI CLI tools. Subclasses must implement tool-specific command building.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the tool name.
        
        Returns:
            Tool name identifier
        """
        ...

    @property
    @abstractmethod
    def command(self) -> str:
        """Return the command name to check for availability.
        
        Returns:
            Command name to check in PATH
        """
        ...

    @abstractmethod
    def _build_command_args(self) -> list[str]:
        """Build tool-specific command arguments.
        
        Returns:
            List of command arguments to pass to subprocess
        """
        ...

    def is_available(self) -> bool:
        """Check if the tool is available in PATH.

        Returns:
            True if the tool command is found in PATH
        """
        return check_tool_available(self.command)

    def _execute_command(
        self,
        combined_prompt: str,
        timeout: int,
    ) -> str:
        """Execute the CLI tool command with error handling.
        
        Args:
            combined_prompt: Combined variant and base prompt
            timeout: Command timeout in seconds
            
        Returns:
            Command output stripped of whitespace
            
        Raises:
            CLIToolError: If command execution fails
        """
        try:
            result = subprocess.run(
                self._build_command_args(),
                input=combined_prompt,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.TimeoutExpired as e:
            raise CLIToolError(
                f"{self.name} timed out after {timeout}s"
            ) from e
        except subprocess.CalledProcessError as e:
            raise CLIToolError(f"{self.name} failed: {e.stderr}") from e
        except Exception as e:
            raise CLIToolError(
                f"{self.name} invocation failed: {e}"
            ) from e

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
            CLIToolError: If tool invocation fails or tool is not available
        """
        if not self.is_available():
            raise CLIToolError(f"{self.name} is not available in PATH")

        combined_prompt = f"{variant_prompt}\n\nOriginal prompt:\n{base_prompt}"
        return self._execute_command(combined_prompt, timeout)


class CodexCLI(BaseCLITool):
    """OpenAI Codex CLI tool implementation.
    
    Note: Command syntax needs verification with actual tool.
    Currently using placeholder implementation.
    """

    @property
    def name(self) -> str:
        """Return the tool name.
        
        Returns:
            Tool name "codex"
        """
        return "codex"

    @property
    def command(self) -> str:
        """Return the command name to check for availability.
        
        Returns:
            Command name "codex"
        """
        return "codex"

    def _build_command_args(self) -> list[str]:
        """Build Codex-specific command arguments.
        
        Returns:
            List of command arguments for Codex CLI
        """
        return [self.command, "--mode", "command"]


class CopilotCLI(BaseCLITool):
    """GitHub Copilot CLI tool implementation."""

    @property
    def name(self) -> str:
        """Return the tool name.
        
        Returns:
            Tool name "copilot"
        """
        return "copilot"

    @property
    def command(self) -> str:
        """Return the command name to check for availability.
        
        Returns:
            Command name "gh" (uses gh copilot)
        """
        return "gh"  # Uses gh copilot

    def is_available(self) -> bool:
        """Check if GitHub CLI is available.
        
        Returns:
            True if gh command is found in PATH
            
        Note:
            TODO: Check if copilot extension is installed
        """
        # Check if gh is available and has copilot extension
        # TODO: Check if copilot extension is installed
        return check_tool_available("gh")

    def _build_command_args(self) -> list[str]:
        """Build Copilot-specific command arguments.
        
        Returns:
            List of command arguments for GitHub Copilot CLI
        """
        return ["gh", "copilot", "suggest", "-t", "shell"]


class ClaudeCLI(BaseCLITool):
    """Anthropic Claude CLI tool implementation."""

    @property
    def name(self) -> str:
        """Return the tool name.
        
        Returns:
            Tool name "claude"
        """
        return "claude"

    @property
    def command(self) -> str:
        """Return the command name to check for availability.
        
        Returns:
            Command name "claude"
        """
        return "claude"

    def _build_command_args(self) -> list[str]:
        """Build Claude-specific command arguments.
        
        Returns:
            List of command arguments for Claude CLI
        """
        return [self.command]


class GeminiCLI(BaseCLITool):
    """Google Gemini CLI tool implementation."""

    @property
    def name(self) -> str:
        """Return the tool name.
        
        Returns:
            Tool name "gemini"
        """
        return "gemini"

    @property
    def command(self) -> str:
        """Return the command name to check for availability.
        
        Returns:
            Command name "gemini"
        """
        return "gemini"

    def _build_command_args(self) -> list[str]:
        """Build Gemini-specific command arguments.
        
        Returns:
            List of command arguments for Gemini CLI
        """
        return [self.command, "command"]


# Tool registry
AVAILABLE_TOOLS: list[CLITool] = [
    CodexCLI(),
    CopilotCLI(),
    ClaudeCLI(),
    GeminiCLI(),
]


def get_tool_by_name(name: str) -> CLITool | None:
    """Get a CLI tool by name.

    Args:
        name: Tool name

    Returns:
        CLI tool instance or None if not found
    """
    for tool in AVAILABLE_TOOLS:
        if tool.name == name:
            return tool
    return None


def get_available_tools() -> list[CLITool]:
    """Get list of available CLI tools.

    Returns:
        List of tools that are available in PATH
    """
    return [tool for tool in AVAILABLE_TOOLS if tool.is_available()]
