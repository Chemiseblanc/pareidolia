"""Tests for CLI tool abstraction."""

import subprocess
from unittest.mock import MagicMock, Mock, patch

import pytest

from pareidolia.core.exceptions import CLIToolError
from pareidolia.generators.cli_tools import check_tool_available


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
