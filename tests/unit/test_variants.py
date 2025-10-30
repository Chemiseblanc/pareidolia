"""Tests for variant generation."""

from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from pareidolia.core.exceptions import (
    ActionNotFoundError,
    CLIToolError,
    NoAvailableCLIToolError,
    VariantTemplateNotFoundError,
)
from pareidolia.core.models import GenerateConfig
from pareidolia.generators.variants import (
    MAX_TEMPLATE_GENERATION_RETRIES,
    VariantGenerator,
)
from pareidolia.templates.composer import PromptComposer
from pareidolia.templates.engine import Jinja2Engine
from pareidolia.templates.loader import TemplateLoader


@pytest.fixture
def mock_loader() -> Mock:
    """Create a mock template loader."""
    loader = Mock(spec=TemplateLoader)
    return loader


@pytest.fixture
def mock_composer() -> Mock:
    """Create a mock prompt composer."""
    composer = Mock(spec=PromptComposer)
    return composer


@pytest.fixture
def generate_config() -> GenerateConfig:
    """Create a generate configuration."""
    return GenerateConfig(
        tool="copilot",
        library="mylib",
        output_dir=Path("/tmp/output"),
    )


@pytest.fixture
def variant_generator(
    mock_loader: Mock, mock_composer: Mock, generate_config: GenerateConfig
) -> VariantGenerator:
    """Create a variant generator instance."""
    return VariantGenerator(
        loader=mock_loader, composer=mock_composer, generate_config=generate_config
    )


@pytest.fixture
def temp_actions_dir(tmp_path: Path) -> Path:
    """Create a temporary actions directory."""
    actions_dir = tmp_path / "actions"
    actions_dir.mkdir()
    return actions_dir


@pytest.fixture
def mock_cli_tool() -> Mock:
    """Create a mock CLI tool."""
    tool = Mock()
    tool.name = "test-tool"
    tool.is_available.return_value = True
    tool.generate_variant.return_value = "Generated variant content"
    return tool


class TestVariantGeneratorInitialization:
    """Tests for VariantGenerator initialization."""

    def test_initialization_with_loader_and_composer(
        self, mock_loader: Mock, mock_composer: Mock, generate_config: GenerateConfig
    ) -> None:
        """Test that generator initializes with required dependencies."""
        generator = VariantGenerator(
            loader=mock_loader, composer=mock_composer, generate_config=generate_config
        )

        assert generator.loader is mock_loader
        assert generator.composer is mock_composer
        assert generator.generate_config is generate_config
        assert isinstance(generator.engine, Jinja2Engine)

    def test_initialization_without_generate_config(
        self, mock_loader: Mock, mock_composer: Mock
    ) -> None:
        """Test that generator initializes without generate_config."""
        generator = VariantGenerator(loader=mock_loader, composer=mock_composer)

        assert generator.loader is mock_loader
        assert generator.composer is mock_composer
        assert generator.generate_config is None
        assert isinstance(generator.engine, Jinja2Engine)


class TestSelectTool:
    """Tests for tool selection logic."""

    @patch("pareidolia.generators.variants.get_tool_by_name")
    def test_select_tool_with_specific_tool_available(
        self,
        mock_get_tool: Mock,
        variant_generator: VariantGenerator,
        mock_cli_tool: Mock,
    ) -> None:
        """Test selecting a specific tool that is available."""
        mock_get_tool.return_value = mock_cli_tool
        mock_cli_tool.is_available.return_value = True

        result = variant_generator._select_tool("test-tool")

        assert result is mock_cli_tool
        mock_get_tool.assert_called_once_with("test-tool")
        mock_cli_tool.is_available.assert_called_once()

    @patch("pareidolia.generators.variants.get_tool_by_name")
    def test_select_tool_with_specific_tool_not_found(
        self, mock_get_tool: Mock, variant_generator: VariantGenerator
    ) -> None:
        """Test selecting a specific tool that doesn't exist."""
        mock_get_tool.return_value = None

        with pytest.raises(
            NoAvailableCLIToolError, match="CLI tool not found: nonexistent"
        ):
            variant_generator._select_tool("nonexistent")

    @patch("pareidolia.generators.variants.get_tool_by_name")
    def test_select_tool_with_specific_tool_not_available(
        self,
        mock_get_tool: Mock,
        variant_generator: VariantGenerator,
        mock_cli_tool: Mock,
    ) -> None:
        """Test selecting a specific tool that is not available."""
        mock_get_tool.return_value = mock_cli_tool
        mock_cli_tool.is_available.return_value = False

        with pytest.raises(
            NoAvailableCLIToolError, match="CLI tool not available: test-tool"
        ):
            variant_generator._select_tool("test-tool")

    @patch("pareidolia.generators.variants.get_available_tools")
    def test_select_tool_auto_detect_with_available_tools(
        self,
        mock_get_available: Mock,
        variant_generator: VariantGenerator,
        mock_cli_tool: Mock,
    ) -> None:
        """Test auto-detecting when tools are available."""
        mock_get_available.return_value = [mock_cli_tool]

        result = variant_generator._select_tool(None)

        assert result is mock_cli_tool
        mock_get_available.assert_called_once()

    @patch("pareidolia.generators.variants.get_available_tools")
    def test_select_tool_auto_detect_with_no_available_tools(
        self, mock_get_available: Mock, variant_generator: VariantGenerator
    ) -> None:
        """Test auto-detecting when no tools are available."""
        mock_get_available.return_value = []

        with pytest.raises(
            NoAvailableCLIToolError, match="No AI CLI tools available"
        ):
            variant_generator._select_tool(None)

    @patch("pareidolia.generators.variants.get_available_tools")
    def test_select_tool_auto_detect_selects_first_available(
        self, mock_get_available: Mock, variant_generator: VariantGenerator
    ) -> None:
        """Test that auto-detect selects the first available tool."""
        tool1 = Mock()
        tool1.name = "tool1"
        tool2 = Mock()
        tool2.name = "tool2"
        mock_get_available.return_value = [tool1, tool2]

        result = variant_generator._select_tool(None)

        assert result is tool1

    @patch("pareidolia.generators.variants.get_available_tools")
    @patch("pareidolia.generators.variants.logger")
    def test_select_tool_auto_detect_logs_selected_tool(
        self,
        mock_logger: Mock,
        mock_get_available: Mock,
        variant_generator: VariantGenerator,
        mock_cli_tool: Mock,
    ) -> None:
        """Test that auto-detect logs the selected tool."""
        mock_get_available.return_value = [mock_cli_tool]

        variant_generator._select_tool(None)

        mock_logger.info.assert_called_once_with("Using CLI tool: test-tool")


class TestGenerateSingleVariantCLI:
    """Tests for single variant template generation using CLI strategy."""

    def test_generate_single_variant_cli_success(
        self,
        variant_generator: VariantGenerator,
        mock_loader: Mock,
        mock_cli_tool: Mock,
        temp_actions_dir: Path,
    ) -> None:
        """Test successful generation of a variant template using CLI."""
        # Mock action template loading
        action_mock = Mock()
        action_mock.template = "{{ persona }}\n\nResearch this topic.\n{{ tool }}"
        mock_loader.load_action.return_value = action_mock
        mock_loader.root = temp_actions_dir

        # Mock variant instruction template
        mock_loader.load_variant_template.return_value = (
            "Transform to {{ variant_name }} variant for {{ action_name }}"
        )

        # Mock CLI tool response with valid template
        generated_template = (
            "{{ persona }}\n\nUpdate this research.\n{{ tool }}\n{{ library }}"
        )
        mock_cli_tool.generate_variant.return_value = generated_template

        with patch(
            "pareidolia.generators.variants.get_available_tools",
            return_value=[mock_cli_tool],
        ):
            result = variant_generator.generate_single_variant(
                variant_name="update",
                action_name="research",
                persona_name="test_persona",
                strategy="cli",
            )

        # Verify template file was created
        assert result.exists()
        assert result.name == "update-research.md.j2"
        assert result.read_text() == generated_template

        # Verify action was loaded with test persona
        mock_loader.load_action.assert_called_once_with("research", "test_persona")

        # Verify variant instructions were loaded and rendered
        mock_loader.load_variant_template.assert_called_once_with("update")

        # Verify CLI tool was called
        mock_cli_tool.generate_variant.assert_called_once()

    def test_generate_single_variant_renders_variant_instructions(
        self,
        variant_generator: VariantGenerator,
        mock_loader: Mock,
        mock_cli_tool: Mock,
        temp_actions_dir: Path,
    ) -> None:
        """Test that variant instructions are rendered with correct context."""
        action_mock = Mock()
        action_mock.template = "{{ persona }}\n\nBase action."
        mock_loader.load_action.return_value = action_mock
        mock_loader.root = temp_actions_dir

        # Variant instructions with placeholders
        variant_instructions = (
            "Action: {{ action_name }}, Variant: {{ variant_name }}, "
            "Tool: {{ tool }}, Library: {{ library }}"
        )
        mock_loader.load_variant_template.return_value = variant_instructions

        # Valid generated template
        mock_cli_tool.generate_variant.return_value = (
            "{{ persona }}\n\nRefined action.\n{{ tool }}"
        )

        with patch(
            "pareidolia.generators.variants.get_available_tools",
            return_value=[mock_cli_tool],
        ):
            variant_generator.generate_single_variant(
                variant_name="refine",
                action_name="code",
                persona_name="test_persona",
                strategy="cli",
            )

        # Check that the variant instructions were rendered with correct context
        call_args = mock_cli_tool.generate_variant.call_args
        variant_prompt = call_args[1]["variant_prompt"]
        assert "Action: code" in variant_prompt
        assert "Variant: refine" in variant_prompt
        assert "Tool: copilot" in variant_prompt
        assert "Library: mylib" in variant_prompt

    def test_generate_single_variant_action_not_found(
        self,
        variant_generator: VariantGenerator,
        mock_loader: Mock,
    ) -> None:
        """Test handling when action template is not found."""
        mock_loader.load_action.side_effect = ActionNotFoundError(
            "Action not found: missing"
        )

        with pytest.raises(ActionNotFoundError):
            variant_generator.generate_single_variant(
                variant_name="update",
                action_name="missing",
                persona_name="test_persona",
                strategy="cli",
            )

    def test_generate_single_variant_variant_template_not_found(
        self,
        variant_generator: VariantGenerator,
        mock_loader: Mock,
    ) -> None:
        """Test handling when variant instruction template is not found."""
        action_mock = Mock()
        action_mock.template = "{{ persona }}\n\nBase action."
        mock_loader.load_action.return_value = action_mock

        mock_loader.load_variant_template.side_effect = VariantTemplateNotFoundError(
            "Template not found"
        )

        with pytest.raises(VariantTemplateNotFoundError):
            variant_generator.generate_single_variant(
                variant_name="missing",
                action_name="research",
                persona_name="test_persona",
                strategy="cli",
            )

    def test_generate_single_variant_cli_tool_error_after_retries(
        self,
        variant_generator: VariantGenerator,
        mock_loader: Mock,
        mock_cli_tool: Mock,
        temp_actions_dir: Path,
    ) -> None:
        """Test handling when CLI tool fails after all retries."""
        action_mock = Mock()
        action_mock.template = "{{ persona }}\n\nBase action."
        mock_loader.load_action.return_value = action_mock
        mock_loader.root = temp_actions_dir
        mock_loader.load_variant_template.return_value = "Transform to update"

        mock_cli_tool.generate_variant.side_effect = CLIToolError("Tool failed")

        with patch(
            "pareidolia.generators.variants.get_available_tools",
            return_value=[mock_cli_tool],
        ), pytest.raises(CLIToolError, match="Tool failed"):
            variant_generator.generate_single_variant(
                variant_name="update",
                action_name="research",
                persona_name="test_persona",
                strategy="cli",
            )

        # Verify retries happened
        assert (
            mock_cli_tool.generate_variant.call_count
            == MAX_TEMPLATE_GENERATION_RETRIES
        )


    def test_generate_single_variant_validation_missing_placeholder(
        self,
        variant_generator: VariantGenerator,
        mock_loader: Mock,
        mock_cli_tool: Mock,
        temp_actions_dir: Path,
    ) -> None:
        """Test that invalid templates are retried."""
        action_mock = Mock()
        action_mock.template = "{{ persona }}\n\nBase action."
        mock_loader.load_action.return_value = action_mock
        mock_loader.root = temp_actions_dir
        mock_loader.load_variant_template.return_value = "Transform to update"

        # First attempts return invalid templates (missing {{ persona }})
        # Final attempt returns valid template
        mock_cli_tool.generate_variant.side_effect = [
            "Invalid template without placeholder",
            "Still invalid",
            "{{ persona }}\n\nValid template\n{{ tool }}",
        ]

        with patch(
            "pareidolia.generators.variants.get_available_tools",
            return_value=[mock_cli_tool],
        ):
            result = variant_generator.generate_single_variant(
                variant_name="update",
                action_name="research",
                persona_name="test_persona",
                strategy="cli",
            )

        # Should succeed on third attempt
        assert result.exists()
        assert "{{ persona }}" in result.read_text()
        assert mock_cli_tool.generate_variant.call_count == 3

    def test_generate_single_variant_validation_fails_all_retries(
        self,
        variant_generator: VariantGenerator,
        mock_loader: Mock,
        mock_cli_tool: Mock,
        temp_actions_dir: Path,
    ) -> None:
        """Test that generation fails after all retry attempts."""
        action_mock = Mock()
        action_mock.template = "{{ persona }}\n\nBase action."
        mock_loader.load_action.return_value = action_mock
        mock_loader.root = temp_actions_dir
        mock_loader.load_variant_template.return_value = "Transform to update"

        # All attempts return invalid templates
        mock_cli_tool.generate_variant.return_value = "Invalid template"

        with patch(
            "pareidolia.generators.variants.get_available_tools",
            return_value=[mock_cli_tool],
        ), pytest.raises(CLIToolError, match="Failed to generate valid template"):
            variant_generator.generate_single_variant(
                variant_name="update",
                action_name="research",
                persona_name="test_persona",
                strategy="cli",
                )

        assert (
            mock_cli_tool.generate_variant.call_count
            == MAX_TEMPLATE_GENERATION_RETRIES
        )

    def test_generate_single_variant_template_written_to_correct_location(
        self,
        variant_generator: VariantGenerator,
        mock_loader: Mock,
        mock_cli_tool: Mock,
        tmp_path: Path,
    ) -> None:
        """Test that template is written to actions/{variant}-{action}.md.j2."""
        # Setup: loader.root points to project root
        project_root = tmp_path / "project"
        project_root.mkdir()
        actions_dir = project_root / "actions"
        actions_dir.mkdir()

        action_mock = Mock()
        action_mock.template = "{{ persona }}\n\nBase action."
        mock_loader.load_action.return_value = action_mock
        mock_loader.root = project_root  # root is project root
        mock_loader.load_variant_template.return_value = "Transform to refine"

        generated_template = "{{ persona }}\n\nRefined action."
        mock_cli_tool.generate_variant.return_value = generated_template

        with patch(
            "pareidolia.generators.variants.get_available_tools",
            return_value=[mock_cli_tool],
        ):
            result = variant_generator.generate_single_variant(
                variant_name="refine",
                action_name="code",
                persona_name="test_persona",
                strategy="cli",
            )

        expected_path = actions_dir / "refine-code.md.j2"
        assert result == expected_path
        assert expected_path.exists()
        assert expected_path.read_text() == generated_template

    def test_generate_single_variant_preserves_jinja2_placeholders(
        self,
        variant_generator: VariantGenerator,
        mock_loader: Mock,
        mock_cli_tool: Mock,
        temp_actions_dir: Path,
    ) -> None:
        """Test that generated templates preserve Jinja2 placeholders."""
        action_mock = Mock()
        action_mock.template = (
            "{{ persona }}\n\nResearch with {{ tool }} and {{ library }}"
        )
        mock_loader.load_action.return_value = action_mock
        mock_loader.root = temp_actions_dir
        mock_loader.load_variant_template.return_value = "Transform to update"

        # Generated template should preserve all placeholders
        generated_template = (
            "{{ persona }}\n\nUpdate research using {{ tool }} and {{ library }}"
        )
        mock_cli_tool.generate_variant.return_value = generated_template

        with patch(
            "pareidolia.generators.variants.get_available_tools",
            return_value=[mock_cli_tool],
        ):
            result = variant_generator.generate_single_variant(
                variant_name="update",
                action_name="research",
                persona_name="test_persona",
                strategy="cli",
            )

        content = result.read_text()
        assert "{{ persona }}" in content
        assert "{{ tool }}" in content
        assert "{{ library }}" in content


class TestGenerateSingleVariantMCP:
    """Tests for single variant template generation using MCP strategy."""

    def test_generate_single_variant_mcp_success(
        self,
        variant_generator: VariantGenerator,
        mock_loader: Mock,
        temp_actions_dir: Path,
    ) -> None:
        """Test successful generation using MCP strategy."""
        action_mock = Mock()
        action_mock.template = "{{ persona }}\n\nBase action."
        mock_loader.load_action.return_value = action_mock
        mock_loader.root = temp_actions_dir
        mock_loader.load_variant_template.return_value = "Transform to update"

        # Mock MCP context with async sample method
        mock_ctx = Mock()
        mock_response = Mock()
        mock_response.text = "{{ persona }}\n\nUpdated action via MCP."

        # Create an async mock for sample
        async_sample = AsyncMock(return_value=mock_response)
        mock_ctx.sample = async_sample

        result = variant_generator.generate_single_variant(
            variant_name="update",
            action_name="research",
            persona_name="test_persona",
            strategy="mcp",
            ctx=mock_ctx,
        )

        # Verify template was created
        assert result.exists()
        assert result.name == "update-research.md.j2"
        assert "{{ persona }}" in result.read_text()

        # Verify sample was called
        async_sample.assert_called_once()

    def test_generate_single_variant_mcp_requires_ctx(
        self,
        variant_generator: VariantGenerator,
        mock_loader: Mock,
    ) -> None:
        """Test that MCP strategy requires ctx parameter."""
        action_mock = Mock()
        action_mock.template = "{{ persona }}\n\nBase action."
        mock_loader.load_action.return_value = action_mock
        mock_loader.load_variant_template.return_value = "Transform to update"

        with pytest.raises(ValueError, match="ctx parameter required"):
            variant_generator.generate_single_variant(
                variant_name="update",
                action_name="research",
                persona_name="test_persona",
                strategy="mcp",
                ctx=None,
            )

    def test_generate_single_variant_mcp_validation_and_retry(
        self,
        variant_generator: VariantGenerator,
        mock_loader: Mock,
        temp_actions_dir: Path,
    ) -> None:
        """Test that MCP strategy also validates and retries."""
        action_mock = Mock()
        action_mock.template = "{{ persona }}\n\nBase action."
        mock_loader.load_action.return_value = action_mock
        mock_loader.root = temp_actions_dir
        mock_loader.load_variant_template.return_value = "Transform to update"

        # Mock MCP context
        mock_ctx = Mock()

        # First response invalid, second valid
        response1 = Mock()
        response1.text = "Invalid template without placeholder"
        response2 = Mock()
        response2.text = "{{ persona }}\n\nValid template."

        async_sample = AsyncMock(side_effect=[response1, response2])
        mock_ctx.sample = async_sample

        result = variant_generator.generate_single_variant(
            variant_name="update",
            action_name="research",
            persona_name="test_persona",
            strategy="mcp",
            ctx=mock_ctx,
        )

        # Should succeed on second attempt
        assert result.exists()
        assert "{{ persona }}" in result.read_text()
        assert async_sample.call_count == 2


class TestMaxTemplateGenerationRetries:
    """Tests for MAX_TEMPLATE_GENERATION_RETRIES constant usage."""

    def test_max_retries_constant_is_defined(self) -> None:
        """Test that MAX_TEMPLATE_GENERATION_RETRIES constant is defined."""
        assert MAX_TEMPLATE_GENERATION_RETRIES == 3

    def test_retries_respect_max_constant(
        self,
        variant_generator: VariantGenerator,
        mock_loader: Mock,
        mock_cli_tool: Mock,
        temp_actions_dir: Path,
    ) -> None:
        """Test that retries do not exceed MAX_TEMPLATE_GENERATION_RETRIES."""
        action_mock = Mock()
        action_mock.template = "{{ persona }}\n\nBase action."
        mock_loader.load_action.return_value = action_mock
        mock_loader.root = temp_actions_dir
        mock_loader.load_variant_template.return_value = "Transform"

        # Always return invalid template
        mock_cli_tool.generate_variant.return_value = "Invalid"

        with patch(
            "pareidolia.generators.variants.get_available_tools",
            return_value=[mock_cli_tool],
        ), pytest.raises(CLIToolError):
            variant_generator.generate_single_variant(
                variant_name="update",
                action_name="research",
                persona_name="test_persona",
                strategy="cli",
            )

        # Should be called exactly MAX_TEMPLATE_GENERATION_RETRIES times
        assert (
            mock_cli_tool.generate_variant.call_count
            == MAX_TEMPLATE_GENERATION_RETRIES
        )
