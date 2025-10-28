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


class CodexCLI:
    """OpenAI Codex CLI tool implementation."""

    @property
    def name(self) -> str:
        return "codex"

    @property
    def command(self) -> str:
        return "codex"

    def is_available(self) -> bool:
        return check_tool_available(self.command)

    def generate_variant(
        self,
        variant_prompt: str,
        base_prompt: str,
        timeout: int = 60,
    ) -> str:
        """Generate variant using Codex CLI.

        Note: Command syntax needs verification with actual tool.
        Currently using placeholder implementation.
        """
        if not self.is_available():
            raise CLIToolError(f"{self.name} is not available in PATH")

        # Combine prompts - may need adjustment based on actual tool
        combined_prompt = f"{variant_prompt}\n\nOriginal prompt:\n{base_prompt}"

        try:
            result = subprocess.run(
                [self.command, "--mode", "command"],
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


class CopilotCLI:
    """GitHub Copilot CLI tool implementation."""

    @property
    def name(self) -> str:
        return "copilot"

    @property
    def command(self) -> str:
        return "gh"  # Uses gh copilot

    def is_available(self) -> bool:
        # Check if gh is available and has copilot extension
        # TODO: Check if copilot extension is installed
        return check_tool_available("gh")

    def generate_variant(
        self,
        variant_prompt: str,
        base_prompt: str,
        timeout: int = 60,
    ) -> str:
        """Generate variant using GitHub Copilot CLI."""
        if not self.is_available():
            raise CLIToolError(f"{self.name} is not available")

        combined_prompt = f"{variant_prompt}\n\nOriginal prompt:\n{base_prompt}"

        try:
            result = subprocess.run(
                ["gh", "copilot", "suggest", "-t", "shell"],
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


class ClaudeCLI:
    """Anthropic Claude CLI tool implementation."""

    @property
    def name(self) -> str:
        return "claude"

    @property
    def command(self) -> str:
        return "claude"

    def is_available(self) -> bool:
        return check_tool_available(self.command)

    def generate_variant(
        self,
        variant_prompt: str,
        base_prompt: str,
        timeout: int = 60,
    ) -> str:
        """Generate variant using Claude CLI."""
        if not self.is_available():
            raise CLIToolError(f"{self.name} is not available in PATH")

        combined_prompt = f"{variant_prompt}\n\nOriginal prompt:\n{base_prompt}"

        try:
            result = subprocess.run(
                [self.command],
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


class GeminiCLI:
    """Google Gemini CLI tool implementation."""

    @property
    def name(self) -> str:
        return "gemini"

    @property
    def command(self) -> str:
        return "gemini"

    def is_available(self) -> bool:
        return check_tool_available(self.command)

    def generate_variant(
        self,
        variant_prompt: str,
        base_prompt: str,
        timeout: int = 60,
    ) -> str:
        """Generate variant using Gemini CLI."""
        if not self.is_available():
            raise CLIToolError(f"{self.name} is not available in PATH")

        combined_prompt = f"{variant_prompt}\n\nOriginal prompt:\n{base_prompt}"

        try:
            result = subprocess.run(
                [self.command, "command"],
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
