"""Unit tests for naming convention adapters."""

from pathlib import Path

import pytest

from pareidolia.generators.naming import (
    ClaudeCodeNaming,
    CopilotNaming,
    StandardNaming,
    ToolAdapter,
)


@pytest.fixture(autouse=True, scope="function")
def clear_registry() -> None:
    """Clear and repopulate the adapter registry before each test.

    This ensures test isolation by preventing state leakage between tests.
    The registry is repopulated after clearing by triggering the
    __init_subclass__ mechanism through import.
    """
    # Clear the registry
    ToolAdapter._clear_registry()

    # Force re-registration by accessing the class registry
    # The classes are already defined, so we need to manually re-register them
    StandardNaming._registry[StandardNaming().name] = StandardNaming()
    CopilotNaming._registry[CopilotNaming().name] = CopilotNaming()
    ClaudeCodeNaming._registry[ClaudeCodeNaming().name] = ClaudeCodeNaming()


class TestStandardNaming:
    """Tests for StandardNaming adapter."""

    def test_name_property(self) -> None:
        """Test that name property returns correct identifier."""
        adapter = StandardNaming()
        assert adapter.name == "standard"

    def test_description_property(self) -> None:
        """Test that description property returns correct text."""
        adapter = StandardNaming()
        assert adapter.description == "Standard format (.prompt.md)"

    def test_file_extension_property(self) -> None:
        """Test that file_extension property returns correct extension."""
        adapter = StandardNaming()
        assert adapter.file_extension == ".prompt.md"

    def test_get_filename_without_library(self) -> None:
        """Test filename generation without library."""
        adapter = StandardNaming()
        filename = adapter.get_filename("research")
        assert filename == "research.prompt.md"

    def test_get_filename_with_library(self) -> None:
        """Test filename generation with library (ignored for standard)."""
        adapter = StandardNaming()
        filename = adapter.get_filename("research", library="mylib")
        # Library is ignored for standard naming
        assert filename == "research.prompt.md"

    def test_get_output_path_without_library(self) -> None:
        """Test output path generation without library."""
        adapter = StandardNaming()
        output_dir = Path("/output")
        path = adapter.get_output_path(output_dir, "research")
        assert path == Path("/output/research.prompt.md")

    def test_get_output_path_with_library(self) -> None:
        """Test output path generation with library."""
        adapter = StandardNaming()
        output_dir = Path("/output")
        path = adapter.get_output_path(output_dir, "research", library="mylib")
        # Library is ignored for standard naming
        assert path == Path("/output/research.prompt.md")


class TestCopilotNaming:
    """Tests for CopilotNaming adapter."""

    def test_name_property(self) -> None:
        """Test that name property returns correct identifier."""
        adapter = CopilotNaming()
        assert adapter.name == "copilot"

    def test_description_property(self) -> None:
        """Test that description property returns correct text."""
        adapter = CopilotNaming()
        assert adapter.description == "GitHub Copilot format (.prompt.md)"

    def test_file_extension_property(self) -> None:
        """Test that file_extension property returns correct extension."""
        adapter = CopilotNaming()
        assert adapter.file_extension == ".prompt.md"

    def test_get_filename_without_library(self) -> None:
        """Test filename generation without library."""
        adapter = CopilotNaming()
        filename = adapter.get_filename("research")
        assert filename == "research.prompt.md"

    def test_get_filename_with_library(self) -> None:
        """Test filename generation with library prefix."""
        adapter = CopilotNaming()
        filename = adapter.get_filename("research", library="mylib")
        assert filename == "mylib.research.prompt.md"

    def test_get_output_path_without_library(self) -> None:
        """Test output path generation without library."""
        adapter = CopilotNaming()
        output_dir = Path("/output")
        path = adapter.get_output_path(output_dir, "research")
        assert path == Path("/output/research.prompt.md")

    def test_get_output_path_with_library(self) -> None:
        """Test output path generation with library (flat structure)."""
        adapter = CopilotNaming()
        output_dir = Path("/output")
        path = adapter.get_output_path(output_dir, "research", library="mylib")
        assert path == Path("/output/mylib.research.prompt.md")


class TestClaudeCodeNaming:
    """Tests for ClaudeCodeNaming adapter."""

    def test_name_property(self) -> None:
        """Test that name property returns correct identifier."""
        adapter = ClaudeCodeNaming()
        assert adapter.name == "claude-code"

    def test_description_property(self) -> None:
        """Test that description property returns correct text."""
        adapter = ClaudeCodeNaming()
        assert adapter.description == "Claude Code format (.md)"

    def test_file_extension_property(self) -> None:
        """Test that file_extension property returns correct extension."""
        adapter = ClaudeCodeNaming()
        assert adapter.file_extension == ".md"

    def test_get_filename_without_library(self) -> None:
        """Test filename generation without library."""
        adapter = ClaudeCodeNaming()
        filename = adapter.get_filename("research")
        assert filename == "research.md"

    def test_get_filename_with_library(self) -> None:
        """Test filename generation with library (no prefix in filename)."""
        adapter = ClaudeCodeNaming()
        filename = adapter.get_filename("research", library="mylib")
        # Library creates subdirectory, not filename prefix
        assert filename == "research.md"

    def test_get_output_path_without_library(self) -> None:
        """Test output path generation without library."""
        adapter = ClaudeCodeNaming()
        output_dir = Path("/output")
        path = adapter.get_output_path(output_dir, "research")
        assert path == Path("/output/research.md")

    def test_get_output_path_with_library(self) -> None:
        """Test output path generation with library (subdirectory structure)."""
        adapter = ClaudeCodeNaming()
        output_dir = Path("/output")
        path = adapter.get_output_path(output_dir, "research", library="mylib")
        assert path == Path("/output/mylib/research.md")


class TestToolAdapterRegistry:
    """Tests for ToolAdapter registry operations."""

    def test_get_adapter_standard(self) -> None:
        """Test getting standard adapter from registry."""
        adapter = ToolAdapter.get_adapter("standard")
        assert isinstance(adapter, StandardNaming)
        assert adapter.name == "standard"

    def test_get_adapter_copilot(self) -> None:
        """Test getting copilot adapter from registry."""
        adapter = ToolAdapter.get_adapter("copilot")
        assert isinstance(adapter, CopilotNaming)
        assert adapter.name == "copilot"

    def test_get_adapter_claude_code(self) -> None:
        """Test getting claude-code adapter from registry."""
        adapter = ToolAdapter.get_adapter("claude-code")
        assert isinstance(adapter, ClaudeCodeNaming)
        assert adapter.name == "claude-code"

    def test_get_adapter_invalid_name(self) -> None:
        """Test that getting invalid adapter raises helpful error."""
        with pytest.raises(ValueError) as exc_info:
            ToolAdapter.get_adapter("invalid-tool")

        error_msg = str(exc_info.value)
        assert "Unknown tool 'invalid-tool'" in error_msg
        assert "Available:" in error_msg
        assert "standard" in error_msg
        assert "copilot" in error_msg
        assert "claude-code" in error_msg

    def test_list_available(self) -> None:
        """Test listing all available adapters."""
        available = ToolAdapter.list_available()

        assert len(available) == 3
        assert "standard" in available
        assert "copilot" in available
        assert "claude-code" in available

        assert isinstance(available["standard"], StandardNaming)
        assert isinstance(available["copilot"], CopilotNaming)
        assert isinstance(available["claude-code"], ClaudeCodeNaming)

    def test_is_supported_valid_names(self) -> None:
        """Test that valid tool names are supported."""
        assert ToolAdapter.is_supported("standard") is True
        assert ToolAdapter.is_supported("copilot") is True
        assert ToolAdapter.is_supported("claude-code") is True

    def test_is_supported_invalid_names(self) -> None:
        """Test that invalid tool names are not supported."""
        assert ToolAdapter.is_supported("invalid") is False
        assert ToolAdapter.is_supported("unknown-tool") is False
        assert ToolAdapter.is_supported("") is False

    def test_registry_returns_same_instance(self) -> None:
        """Test that registry returns the same adapter instance."""
        adapter1 = ToolAdapter.get_adapter("standard")
        adapter2 = ToolAdapter.get_adapter("standard")
        assert adapter1 is adapter2


@pytest.mark.parametrize(
    "adapter_class,expected_name,expected_extension",
    [
        (StandardNaming, "standard", ".prompt.md"),
        (CopilotNaming, "copilot", ".prompt.md"),
        (ClaudeCodeNaming, "claude-code", ".md"),
    ],
)
class TestAdapterProperties:
    """Parametrized tests for adapter properties."""

    def test_adapter_properties(
        self,
        adapter_class: type[ToolAdapter],
        expected_name: str,
        expected_extension: str,
    ) -> None:
        """Test that adapter has correct name and extension properties."""
        adapter = adapter_class()
        assert adapter.name == expected_name
        assert adapter.file_extension == expected_extension
        assert len(adapter.description) > 0


@pytest.mark.parametrize(
    "adapter_class,action,library,expected_filename",
    [
        (StandardNaming, "research", None, "research.prompt.md"),
        (StandardNaming, "research", "mylib", "research.prompt.md"),
        (CopilotNaming, "research", None, "research.prompt.md"),
        (CopilotNaming, "research", "mylib", "mylib.research.prompt.md"),
        (ClaudeCodeNaming, "research", None, "research.md"),
        (ClaudeCodeNaming, "research", "mylib", "research.md"),
    ],
)
class TestAdapterFilenames:
    """Parametrized tests for filename generation."""

    def test_get_filename(
        self,
        adapter_class: type[ToolAdapter],
        action: str,
        library: str | None,
        expected_filename: str,
    ) -> None:
        """Test that adapter generates correct filename."""
        adapter = adapter_class()
        filename = adapter.get_filename(action, library)
        assert filename == expected_filename


class TestGenerateConfigValidation:
    """Tests for GenerateConfig validation with ToolAdapter."""

    def test_valid_tool_names(self) -> None:
        """Test that valid tool names pass validation."""
        from pareidolia.core.models import GenerateConfig

        # All these should succeed
        config1 = GenerateConfig(
            tool="standard",
            library=None,
            output_dir=Path("output"),
        )
        assert config1.tool == "standard"

        config2 = GenerateConfig(
            tool="copilot",
            library=None,
            output_dir=Path("output"),
        )
        assert config2.tool == "copilot"

        config3 = GenerateConfig(
            tool="claude-code",
            library=None,
            output_dir=Path("output"),
        )
        assert config3.tool == "claude-code"

    def test_invalid_tool_name(self) -> None:
        """Test that invalid tool name raises helpful error."""
        from pareidolia.core.models import GenerateConfig

        with pytest.raises(ValueError) as exc_info:
            GenerateConfig(
                tool="invalid-tool",
                library=None,
                output_dir=Path("output"),
            )

        error_msg = str(exc_info.value)
        assert "Unsupported tool 'invalid-tool'" in error_msg
        assert "Available tools:" in error_msg
        assert "standard" in error_msg
        assert "copilot" in error_msg
        assert "claude-code" in error_msg
