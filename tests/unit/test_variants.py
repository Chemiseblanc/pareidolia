"""Tests for variant generation."""

from unittest.mock import Mock, patch

import pytest

from pareidolia.core.exceptions import (
    CLIToolError,
    NoAvailableCLIToolError,
    VariantTemplateNotFoundError,
)
from pareidolia.core.models import PromptConfig
from pareidolia.generators.variants import VariantGenerator
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
def variant_generator(mock_loader: Mock, mock_composer: Mock) -> VariantGenerator:
    """Create a variant generator instance."""
    return VariantGenerator(loader=mock_loader, composer=mock_composer)


@pytest.fixture
def prompt_config() -> PromptConfig:
    """Create a prompt configuration."""
    return PromptConfig(
        persona="researcher",
        action="research",
        variants=["update", "refine"],
        cli_tool=None,
    )


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
        self, mock_loader: Mock, mock_composer: Mock
    ) -> None:
        """Test that generator initializes with required dependencies."""
        generator = VariantGenerator(loader=mock_loader, composer=mock_composer)

        assert generator.loader is mock_loader
        assert generator.composer is mock_composer
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


class TestGenerateSingleVariant:
    """Tests for single variant generation."""

    def test_generate_single_variant_success(
        self,
        variant_generator: VariantGenerator,
        mock_loader: Mock,
        mock_cli_tool: Mock,
    ) -> None:
        """Test successful generation of a single variant."""
        mock_loader.load_variant_template.return_value = (
            "Transform the prompt: {{ variant_name }}"
        )
        mock_cli_tool.generate_variant.return_value = "Generated content"

        result = variant_generator.generate_single_variant(
            variant_name="update",
            persona_name="researcher",
            action_name="research",
            base_prompt="Base prompt content",
            tool=mock_cli_tool,
            timeout=60,
        )

        assert result == "Generated content"
        mock_loader.load_variant_template.assert_called_once_with("update")
        mock_cli_tool.generate_variant.assert_called_once()

        # Verify the call arguments
        call_args = mock_cli_tool.generate_variant.call_args
        assert call_args[1]["base_prompt"] == "Base prompt content"
        assert call_args[1]["timeout"] == 60
        assert "Transform the prompt: update" in call_args[1]["variant_prompt"]

    def test_generate_single_variant_renders_template_with_context(
        self,
        variant_generator: VariantGenerator,
        mock_loader: Mock,
        mock_cli_tool: Mock,
    ) -> None:
        """Test that variant template is rendered with correct context."""
        template = (
            "Persona: {{ persona_name }}, Action: {{ action_name }}, "
            "Variant: {{ variant_name }}"
        )
        mock_loader.load_variant_template.return_value = template
        mock_cli_tool.generate_variant.return_value = "Generated content"

        variant_generator.generate_single_variant(
            variant_name="refine",
            persona_name="developer",
            action_name="code",
            base_prompt="Base prompt",
            tool=mock_cli_tool,
            timeout=60,
        )

        # Check that the rendered template contains the context
        call_args = mock_cli_tool.generate_variant.call_args
        variant_prompt = call_args[1]["variant_prompt"]
        assert "Persona: developer" in variant_prompt
        assert "Action: code" in variant_prompt
        assert "Variant: refine" in variant_prompt

    def test_generate_single_variant_template_not_found(
        self,
        variant_generator: VariantGenerator,
        mock_loader: Mock,
        mock_cli_tool: Mock,
    ) -> None:
        """Test handling when variant template is not found."""
        mock_loader.load_variant_template.side_effect = VariantTemplateNotFoundError(
            "Template not found"
        )

        with pytest.raises(VariantTemplateNotFoundError):
            variant_generator.generate_single_variant(
                variant_name="missing",
                persona_name="researcher",
                action_name="research",
                base_prompt="Base prompt",
                tool=mock_cli_tool,
                timeout=60,
            )

    def test_generate_single_variant_cli_tool_error(
        self,
        variant_generator: VariantGenerator,
        mock_loader: Mock,
        mock_cli_tool: Mock,
    ) -> None:
        """Test handling when CLI tool fails."""
        mock_loader.load_variant_template.return_value = "Template content"
        mock_cli_tool.generate_variant.side_effect = CLIToolError("Tool failed")

        with pytest.raises(CLIToolError):
            variant_generator.generate_single_variant(
                variant_name="update",
                persona_name="researcher",
                action_name="research",
                base_prompt="Base prompt",
                tool=mock_cli_tool,
                timeout=60,
            )


class TestGenerateVariants:
    """Tests for batch variant generation."""

    @patch("pareidolia.generators.variants.get_available_tools")
    @patch("pareidolia.generators.variants.logger")
    def test_generate_variants_success(
        self,
        mock_logger: Mock,
        mock_get_available: Mock,
        variant_generator: VariantGenerator,
        mock_loader: Mock,
        prompt_config: PromptConfig,
        mock_cli_tool: Mock,
    ) -> None:
        """Test successful generation of multiple variants."""
        mock_get_available.return_value = [mock_cli_tool]
        mock_loader.load_variant_template.return_value = "Template: {{ variant_name }}"
        mock_cli_tool.generate_variant.side_effect = [
            "Updated content",
            "Refined content",
        ]

        result = variant_generator.generate_variants(
            prompt_config=prompt_config,
            base_prompt="Base prompt content",
            timeout=60,
        )

        assert result == {
            "update": "Updated content",
            "refine": "Refined content",
        }
        assert mock_loader.load_variant_template.call_count == 2
        assert mock_cli_tool.generate_variant.call_count == 2

    @patch("pareidolia.generators.variants.get_tool_by_name")
    def test_generate_variants_with_specific_tool(
        self,
        mock_get_tool: Mock,
        variant_generator: VariantGenerator,
        mock_loader: Mock,
        mock_cli_tool: Mock,
    ) -> None:
        """Test generating variants with a specific CLI tool."""
        config = PromptConfig(
            persona="researcher",
            action="research",
            variants=["update"],
            cli_tool="claude",
        )
        mock_get_tool.return_value = mock_cli_tool
        mock_cli_tool.is_available.return_value = True
        mock_loader.load_variant_template.return_value = "Template content"
        mock_cli_tool.generate_variant.return_value = "Generated content"

        result = variant_generator.generate_variants(
            prompt_config=config,
            base_prompt="Base prompt",
            timeout=60,
        )

        assert result == {"update": "Generated content"}
        mock_get_tool.assert_called_once_with("claude")

    @patch("pareidolia.generators.variants.get_available_tools")
    @patch("pareidolia.generators.variants.logger")
    def test_generate_variants_skips_missing_template(
        self,
        mock_logger: Mock,
        mock_get_available: Mock,
        variant_generator: VariantGenerator,
        mock_loader: Mock,
        mock_cli_tool: Mock,
    ) -> None:
        """Test that missing templates are skipped with warning."""
        config = PromptConfig(
            persona="researcher",
            action="research",
            variants=["update", "missing", "refine"],
            cli_tool=None,
        )
        mock_get_available.return_value = [mock_cli_tool]

        # Second call raises exception (missing template)
        mock_loader.load_variant_template.side_effect = [
            "Template 1",
            VariantTemplateNotFoundError("Template not found"),
            "Template 3",
        ]
        mock_cli_tool.generate_variant.side_effect = [
            "Updated content",
            "Refined content",
        ]

        result = variant_generator.generate_variants(
            prompt_config=config,
            base_prompt="Base prompt",
            timeout=60,
        )

        # Only two variants should be generated (missing one skipped)
        assert len(result) == 2
        assert "update" in result
        assert "refine" in result
        assert "missing" not in result

        # Verify warning was logged
        mock_logger.warning.assert_called_once()
        warning_call = mock_logger.warning.call_args[0][0]
        assert "Skipping variant missing" in warning_call

    @patch("pareidolia.generators.variants.get_available_tools")
    @patch("pareidolia.generators.variants.logger")
    def test_generate_variants_continues_on_error(
        self,
        mock_logger: Mock,
        mock_get_available: Mock,
        variant_generator: VariantGenerator,
        mock_loader: Mock,
        mock_cli_tool: Mock,
    ) -> None:
        """Test that generation continues when a variant fails."""
        config = PromptConfig(
            persona="researcher",
            action="research",
            variants=["update", "failing", "refine"],
            cli_tool=None,
        )
        mock_get_available.return_value = [mock_cli_tool]
        mock_loader.load_variant_template.return_value = "Template content"

        # Second call raises CLI error
        mock_cli_tool.generate_variant.side_effect = [
            "Updated content",
            CLIToolError("Tool failed"),
            "Refined content",
        ]

        result = variant_generator.generate_variants(
            prompt_config=config,
            base_prompt="Base prompt",
            timeout=60,
        )

        # Two variants should be generated (failing one skipped)
        assert len(result) == 2
        assert "update" in result
        assert "refine" in result
        assert "failing" not in result

        # Verify error was logged
        mock_logger.error.assert_called_once()
        error_call = mock_logger.error.call_args[0][0]
        assert "Failed to generate variant failing" in error_call

    @patch("pareidolia.generators.variants.get_available_tools")
    @patch("pareidolia.generators.variants.logger")
    def test_generate_variants_logs_success(
        self,
        mock_logger: Mock,
        mock_get_available: Mock,
        variant_generator: VariantGenerator,
        mock_loader: Mock,
        prompt_config: PromptConfig,
        mock_cli_tool: Mock,
    ) -> None:
        """Test that successful variant generation is logged."""
        mock_get_available.return_value = [mock_cli_tool]
        mock_loader.load_variant_template.return_value = "Template content"
        mock_cli_tool.generate_variant.return_value = "Generated content"

        variant_generator.generate_variants(
            prompt_config=prompt_config,
            base_prompt="Base prompt",
            timeout=60,
        )

        # Should log for each successful variant
        assert mock_logger.info.call_count >= 2
        info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        assert any("Generated variant: update" in call for call in info_calls)
        assert any("Generated variant: refine" in call for call in info_calls)

    @patch("pareidolia.generators.variants.get_available_tools")
    def test_generate_variants_empty_list(
        self,
        mock_get_available: Mock,
        variant_generator: VariantGenerator,
        mock_cli_tool: Mock,
    ) -> None:
        """Test generating with empty variant list returns empty dict."""
        # This shouldn't happen due to PromptConfig validation, but test anyway
        config = PromptConfig.__new__(PromptConfig)
        object.__setattr__(config, "persona", "researcher")
        object.__setattr__(config, "action", "research")
        object.__setattr__(config, "variants", [])
        object.__setattr__(config, "cli_tool", None)

        mock_get_available.return_value = [mock_cli_tool]

        result = variant_generator.generate_variants(
            prompt_config=config,
            base_prompt="Base prompt",
            timeout=60,
        )

        assert result == {}

    @patch("pareidolia.generators.variants.get_available_tools")
    def test_generate_variants_custom_timeout(
        self,
        mock_get_available: Mock,
        variant_generator: VariantGenerator,
        mock_loader: Mock,
        prompt_config: PromptConfig,
        mock_cli_tool: Mock,
    ) -> None:
        """Test that custom timeout is passed to CLI tool."""
        mock_get_available.return_value = [mock_cli_tool]
        mock_loader.load_variant_template.return_value = "Template content"
        mock_cli_tool.generate_variant.return_value = "Generated content"

        variant_generator.generate_variants(
            prompt_config=prompt_config,
            base_prompt="Base prompt",
            timeout=120,
        )

        # Check that timeout is passed correctly
        for call in mock_cli_tool.generate_variant.call_args_list:
            assert call[1]["timeout"] == 120
