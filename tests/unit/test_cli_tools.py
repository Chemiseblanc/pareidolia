"""Tests for CLI tool abstraction."""

import subprocess
from unittest.mock import Mock, patch

import pytest

from pareidolia.core.exceptions import CLIToolError
from pareidolia.generators.cli_tools import (
    AVAILABLE_TOOLS,
    BaseCLITool,
    ClaudeCLI,
    CodexCLI,
    CopilotCLI,
    GeminiCLI,
    check_tool_available,
    get_available_tools,
    get_tool_by_name,
)


class TestCheckToolAvailable:
    """Tests for check_tool_available utility function."""

    def test_check_tool_available_for_existing_command(self):
        """Test that check_tool_available returns True for existing command."""
        # Use a command that should exist on all systems
        assert check_tool_available("python") is True

    def test_check_tool_available_for_missing_command(self):
        """Test that check_tool_available returns False for missing command."""
        # Use a command that should not exist
        assert check_tool_available("nonexistent_command_12345") is False

    @patch("pareidolia.generators.cli_tools.shutil.which")
    def test_check_tool_available_uses_shutil_which(self, mock_which):
        """Test that check_tool_available uses shutil.which."""
        mock_which.return_value = "/usr/bin/test"
        result = check_tool_available("test")
        assert result is True
        mock_which.assert_called_once_with("test")

    @patch("pareidolia.generators.cli_tools.shutil.which")
    def test_check_tool_available_returns_false_when_which_returns_none(
        self, mock_which
    ):
        """Test that check_tool_available returns False when which returns None."""
        mock_which.return_value = None
        result = check_tool_available("test")
        assert result is False
        mock_which.assert_called_once_with("test")


class TestCodexCLI:
    """Tests for CodexCLI class."""

    def test_codex_cli_properties(self):
        """Test CodexCLI properties."""
        tool = CodexCLI()
        assert tool.name == "codex"
        assert tool.command == "codex"

    @patch("pareidolia.generators.cli_tools.check_tool_available")
    def test_codex_is_available_checks_command(self, mock_check):
        """Test that is_available checks for codex command."""
        mock_check.return_value = True
        tool = CodexCLI()
        assert tool.is_available() is True
        mock_check.assert_called_once_with("codex")

    @patch("pareidolia.generators.cli_tools.check_tool_available")
    def test_codex_generate_variant_raises_when_unavailable(self, mock_check):
        """Test that generate_variant raises when tool is unavailable."""
        mock_check.return_value = False
        tool = CodexCLI()
        with pytest.raises(CLIToolError, match="codex is not available"):
            tool.generate_variant("variant", "base")

    @patch("pareidolia.generators.cli_tools.check_tool_available")
    @patch("pareidolia.generators.cli_tools.subprocess.run")
    def test_codex_generate_variant_success(self, mock_run, mock_check):
        """Test successful variant generation with Codex."""
        mock_check.return_value = True
        mock_result = Mock()
        mock_result.stdout = "generated variant content\n"
        mock_run.return_value = mock_result

        tool = CodexCLI()
        result = tool.generate_variant("variant prompt", "base prompt")

        assert result == "generated variant content"
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        assert args[0] == ["codex", "--mode", "command"]
        assert "variant prompt" in kwargs["input"]
        assert "base prompt" in kwargs["input"]
        assert kwargs["timeout"] == 60

    @patch("pareidolia.generators.cli_tools.check_tool_available")
    @patch("pareidolia.generators.cli_tools.subprocess.run")
    def test_codex_generate_variant_timeout(self, mock_run, mock_check):
        """Test that generate_variant raises on timeout."""
        mock_check.return_value = True
        mock_run.side_effect = subprocess.TimeoutExpired("codex", 60)

        tool = CodexCLI()
        with pytest.raises(CLIToolError, match="timed out after 60s"):
            tool.generate_variant("variant", "base")

    @patch("pareidolia.generators.cli_tools.check_tool_available")
    @patch("pareidolia.generators.cli_tools.subprocess.run")
    def test_codex_generate_variant_process_error(self, mock_run, mock_check):
        """Test that generate_variant raises on process error."""
        mock_check.return_value = True
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "codex", stderr="error message"
        )

        tool = CodexCLI()
        with pytest.raises(CLIToolError, match="failed: error message"):
            tool.generate_variant("variant", "base")


class TestCopilotCLI:
    """Tests for CopilotCLI class."""

    def test_copilot_cli_properties(self):
        """Test CopilotCLI properties."""
        tool = CopilotCLI()
        assert tool.name == "copilot"
        assert tool.command == "gh"

    @patch("pareidolia.generators.cli_tools.check_tool_available")
    def test_copilot_is_available_checks_gh_command(self, mock_check):
        """Test that is_available checks for gh command."""
        mock_check.return_value = True
        tool = CopilotCLI()
        assert tool.is_available() is True
        mock_check.assert_called_once_with("gh")

    @patch("pareidolia.generators.cli_tools.check_tool_available")
    def test_copilot_is_available_returns_false_when_gh_missing(
        self, mock_check
    ):
        """Test that is_available returns False when gh is missing."""
        mock_check.return_value = False
        tool = CopilotCLI()
        assert tool.is_available() is False

    @patch("pareidolia.generators.cli_tools.check_tool_available")
    def test_copilot_generate_variant_raises_when_unavailable(self, mock_check):
        """Test that generate_variant raises when tool is unavailable."""
        mock_check.return_value = False
        tool = CopilotCLI()
        with pytest.raises(CLIToolError, match="copilot is not available"):
            tool.generate_variant("variant", "base")

    @patch("pareidolia.generators.cli_tools.check_tool_available")
    @patch("pareidolia.generators.cli_tools.subprocess.run")
    def test_copilot_generate_variant_success(self, mock_run, mock_check):
        """Test successful variant generation with Copilot."""
        mock_check.return_value = True
        mock_result = Mock()
        mock_result.stdout = "generated variant\n"
        mock_run.return_value = mock_result

        tool = CopilotCLI()
        result = tool.generate_variant("variant prompt", "base prompt")

        assert result == "generated variant"
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        assert args[0] == ["gh", "copilot", "suggest", "-t", "shell"]


class TestClaudeCLI:
    """Tests for ClaudeCLI class."""

    def test_claude_cli_properties(self):
        """Test ClaudeCLI properties."""
        tool = ClaudeCLI()
        assert tool.name == "claude"
        assert tool.command == "claude"

    @patch("pareidolia.generators.cli_tools.check_tool_available")
    def test_claude_is_available_checks_command(self, mock_check):
        """Test that is_available checks for claude command."""
        mock_check.return_value = True
        tool = ClaudeCLI()
        assert tool.is_available() is True
        mock_check.assert_called_once_with("claude")

    @patch("pareidolia.generators.cli_tools.check_tool_available")
    def test_claude_generate_variant_raises_when_unavailable(self, mock_check):
        """Test that generate_variant raises when tool is unavailable."""
        mock_check.return_value = False
        tool = ClaudeCLI()
        with pytest.raises(CLIToolError, match="claude is not available"):
            tool.generate_variant("variant", "base")

    @patch("pareidolia.generators.cli_tools.check_tool_available")
    @patch("pareidolia.generators.cli_tools.subprocess.run")
    def test_claude_generate_variant_success(self, mock_run, mock_check):
        """Test successful variant generation with Claude."""
        mock_check.return_value = True
        mock_result = Mock()
        mock_result.stdout = "generated variant\n"
        mock_run.return_value = mock_result

        tool = ClaudeCLI()
        result = tool.generate_variant("variant prompt", "base prompt")

        assert result == "generated variant"
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        assert args[0] == ["claude"]


class TestGeminiCLI:
    """Tests for GeminiCLI class."""

    def test_gemini_cli_properties(self):
        """Test GeminiCLI properties."""
        tool = GeminiCLI()
        assert tool.name == "gemini"
        assert tool.command == "gemini"

    @patch("pareidolia.generators.cli_tools.check_tool_available")
    def test_gemini_is_available_checks_command(self, mock_check):
        """Test that is_available checks for gemini command."""
        mock_check.return_value = True
        tool = GeminiCLI()
        assert tool.is_available() is True
        mock_check.assert_called_once_with("gemini")

    @patch("pareidolia.generators.cli_tools.check_tool_available")
    def test_gemini_generate_variant_raises_when_unavailable(self, mock_check):
        """Test that generate_variant raises when tool is unavailable."""
        mock_check.return_value = False
        tool = GeminiCLI()
        with pytest.raises(CLIToolError, match="gemini is not available"):
            tool.generate_variant("variant", "base")

    @patch("pareidolia.generators.cli_tools.check_tool_available")
    @patch("pareidolia.generators.cli_tools.subprocess.run")
    def test_gemini_generate_variant_success(self, mock_run, mock_check):
        """Test successful variant generation with Gemini."""
        mock_check.return_value = True
        mock_result = Mock()
        mock_result.stdout = "generated variant\n"
        mock_run.return_value = mock_result

        tool = GeminiCLI()
        result = tool.generate_variant("variant prompt", "base prompt")

        assert result == "generated variant"
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        assert args[0] == ["gemini", "command"]


class TestToolRegistry:
    """Tests for tool registry functions."""

    def test_available_tools_contains_all_tools(self):
        """Test that AVAILABLE_TOOLS contains all CLI tools."""
        assert len(AVAILABLE_TOOLS) == 4
        tool_names = [tool.name for tool in AVAILABLE_TOOLS]
        assert "codex" in tool_names
        assert "copilot" in tool_names
        assert "claude" in tool_names
        assert "gemini" in tool_names

    def test_get_tool_by_name_returns_correct_tool(self):
        """Test that get_tool_by_name returns the correct tool."""
        codex = get_tool_by_name("codex")
        assert codex is not None
        assert codex.name == "codex"

        copilot = get_tool_by_name("copilot")
        assert copilot is not None
        assert copilot.name == "copilot"

        claude = get_tool_by_name("claude")
        assert claude is not None
        assert claude.name == "claude"

        gemini = get_tool_by_name("gemini")
        assert gemini is not None
        assert gemini.name == "gemini"

    def test_get_tool_by_name_returns_none_for_unknown_tool(self):
        """Test that get_tool_by_name returns None for unknown tool."""
        assert get_tool_by_name("unknown") is None
        assert get_tool_by_name("") is None

    @patch("pareidolia.generators.cli_tools.check_tool_available")
    def test_get_available_tools_returns_only_available(self, mock_check):
        """Test that get_available_tools returns only available tools."""

        def check_available(cmd: str) -> bool:
            # Simulate only claude being available
            return cmd == "claude"

        mock_check.side_effect = check_available

        available = get_available_tools()
        assert len(available) == 1
        assert available[0].name == "claude"

    @patch("pareidolia.generators.cli_tools.check_tool_available")
    def test_get_available_tools_returns_empty_when_none_available(
        self, mock_check
    ):
        """Test that get_available_tools returns empty list when none available."""
        mock_check.return_value = False

        available = get_available_tools()
        assert len(available) == 0

    @patch("pareidolia.generators.cli_tools.check_tool_available")
    def test_get_available_tools_returns_all_when_all_available(
        self, mock_check
    ):
        """Test that get_available_tools returns all tools when available."""
        mock_check.return_value = True

        available = get_available_tools()
        assert len(available) == 4



class TestBaseCLITool:
    """Tests for BaseCLITool abstract base class."""

    def test_cannot_instantiate_directly(self) -> None:
        """Test that BaseCLITool cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseCLITool()  # type: ignore

    def test_subclass_must_implement_abstract_methods(self) -> None:
        """Test that subclass must implement all abstract methods."""

        # Missing name
        class MissingName(BaseCLITool):
            @property
            def command(self) -> str:
                return "test"

            def _build_command_args(self) -> list[str]:
                return ["test"]

        with pytest.raises(TypeError):
            MissingName()  # type: ignore

        # Missing command
        class MissingCommand(BaseCLITool):
            @property
            def name(self) -> str:
                return "test"

            def _build_command_args(self) -> list[str]:
                return ["test"]

        with pytest.raises(TypeError):
            MissingCommand()  # type: ignore

        # Missing _build_command_args
        class MissingBuildArgs(BaseCLITool):
            @property
            def name(self) -> str:
                return "test"

            @property
            def command(self) -> str:
                return "test"

        with pytest.raises(TypeError):
            MissingBuildArgs()  # type: ignore
