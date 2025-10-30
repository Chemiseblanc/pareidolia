"""Unit tests for MCP prompts."""

from pathlib import Path
from unittest.mock import Mock

import pytest

from pareidolia.core.models import PromptConfig
from pareidolia.mcp.prompts import discover_prompts, register_prompts


class TestMCPPrompts:
    """Tests for MCP prompts discovery and registration."""

    @pytest.fixture
    def mock_mcp(self) -> Mock:
        """Create a mock FastMCP instance."""
        mcp = Mock()
        # Store registered prompts
        mcp.registered_prompts = {}

        def prompt_decorator():
            def decorator(func):
                mcp.registered_prompts[func.__name__] = func
                return func

            return decorator

        mcp.prompt = prompt_decorator
        return mcp

    @pytest.fixture
    def mock_generator(self) -> Mock:
        """Create a mock Generator instance."""
        generator = Mock()
        generator.loader = Mock()
        generator.composer = Mock()
        generator.variant_generator = Mock()
        return generator

    @pytest.fixture
    def mock_config(self, tmp_path: Path) -> Mock:
        """Create a mock PareidoliaConfig."""
        config = Mock()
        config.root = tmp_path / "pareidolia"
        config.prompt = []
        return config

    @pytest.fixture
    def mock_config_with_prompts(self, tmp_path: Path) -> Mock:
        """Create a mock PareidoliaConfig with prompt configurations."""
        config = Mock()
        config.root = tmp_path / "pareidolia"
        config.generate = Mock()
        config.generate.tool = "copilot"
        config.generate.library = None

        # Create a prompt config with base and variants
        prompt_config = PromptConfig(
            persona="researcher",
            action="research",
            variants=["update", "refine"],
            metadata={"description": "Research prompt"},
        )

        config.prompt = [prompt_config]
        return config

    def test_discover_prompts_returns_empty_list_when_no_prompts_configured(
        self,
        mock_config: Mock,
    ) -> None:
        """Test discover_prompts returns empty list when config.prompt is empty."""
        prompts = discover_prompts(mock_config)

        assert prompts == []

    def test_discover_prompts_finds_base_prompt(
        self,
        mock_config_with_prompts: Mock,
    ) -> None:
        """Test discover_prompts finds base prompt from config."""
        prompts = discover_prompts(mock_config_with_prompts)

        # Should find 3 prompts: 1 base + 2 variants
        assert len(prompts) == 3

        # Check base prompt
        base_prompt = prompts[0]
        assert base_prompt[0] == "research"  # name
        assert base_prompt[1] == "researcher"  # persona
        assert base_prompt[2] == "research"  # action
        assert base_prompt[3] is None  # examples
        assert base_prompt[4] == {"description": "Research prompt"}  # metadata
        assert base_prompt[5] is None  # variant (None for base)

    def test_discover_prompts_finds_variant_prompts(
        self,
        mock_config_with_prompts: Mock,
    ) -> None:
        """Test discover_prompts finds variant prompts from config."""
        prompts = discover_prompts(mock_config_with_prompts)

        # Check variant prompts
        update_prompt = prompts[1]
        assert update_prompt[0] == "update-research"  # name
        assert update_prompt[1] == "researcher"  # persona
        assert update_prompt[2] == "research"  # action
        assert update_prompt[5] == "update"  # variant

        refine_prompt = prompts[2]
        assert refine_prompt[0] == "refine-research"  # name
        assert refine_prompt[5] == "refine"  # variant

    def test_discover_prompts_with_multiple_prompt_configs(
        self,
        tmp_path: Path,
    ) -> None:
        """Test discover_prompts handles multiple prompt configurations."""
        config = Mock()
        config.root = tmp_path / "pareidolia"

        # Create two prompt configs
        prompt_config1 = PromptConfig(
            persona="researcher",
            action="research",
            variants=["update"],
            metadata={},
        )

        prompt_config2 = PromptConfig(
            persona="developer",
            action="code",
            variants=["refine", "expand"],
            metadata={"description": "Code prompt"},
        )

        config.prompt = [prompt_config1, prompt_config2]

        prompts = discover_prompts(config)

        # Should have: research base + update variant + code base
        # + refine variant + expand variant = 5
        assert len(prompts) == 5

        # Check research prompts
        assert prompts[0][0] == "research"
        assert prompts[1][0] == "update-research"

        # Check code prompts
        assert prompts[2][0] == "code"
        assert prompts[3][0] == "refine-code"
        assert prompts[4][0] == "expand-code"

    def test_discover_prompts_preserves_metadata(
        self,
        tmp_path: Path,
    ) -> None:
        """Test discover_prompts preserves metadata from config."""
        config = Mock()
        config.root = tmp_path / "pareidolia"

        metadata = {
            "description": "Test prompt",
            "chat_mode": True,
            "temperature": 0.7,
            "tags": ["research", "analysis"],
        }

        prompt_config = PromptConfig(
            persona="researcher",
            action="analyze",
            variants=["dummy"],
            metadata=metadata,
        )

        config.prompt = [prompt_config]

        prompts = discover_prompts(config)

        assert len(prompts) == 2  # base + 1 variant
        assert prompts[0][4] == metadata
        assert prompts[1][4] == metadata

    def test_register_prompts_handles_empty_prompt_list(
        self,
        mock_mcp: Mock,
        mock_generator: Mock,
        mock_config: Mock,
    ) -> None:
        """Test register_prompts handles empty prompt list gracefully."""
        # Should not raise an error
        register_prompts(mock_mcp, mock_generator, mock_config)

        # No prompts should be registered
        assert len(mock_mcp.registered_prompts) == 0

    def test_register_prompts_registers_base_prompt(
        self,
        mock_mcp: Mock,
        mock_generator: Mock,
        mock_config_with_prompts: Mock,
    ) -> None:
        """Test register_prompts registers base prompts correctly."""
        register_prompts(mock_mcp, mock_generator, mock_config_with_prompts)

        # Base prompt should be registered
        assert "research" in mock_mcp.registered_prompts

    def test_register_prompts_registers_variant_prompts(
        self,
        mock_mcp: Mock,
        mock_generator: Mock,
        mock_config_with_prompts: Mock,
    ) -> None:
        """Test register_prompts registers variant prompts correctly."""
        register_prompts(mock_mcp, mock_generator, mock_config_with_prompts)

        # Variant prompts should be registered (with underscores in function names)
        assert "update_research" in mock_mcp.registered_prompts
        assert "refine_research" in mock_mcp.registered_prompts

    def test_register_prompts_creates_correct_prompt_count(
        self,
        mock_mcp: Mock,
        mock_generator: Mock,
        tmp_path: Path,
    ) -> None:
        """Test register_prompts creates correct number of prompts."""
        config = Mock()
        config.root = tmp_path / "pareidolia"
        config.generate = Mock()
        config.generate.tool = "copilot"
        config.generate.library = None

        # Create prompt config with 2 variants
        prompt_config = PromptConfig(
            persona="researcher",
            action="research",
            variants=["update", "refine"],
            metadata={},
        )

        config.prompt = [prompt_config]

        register_prompts(mock_mcp, mock_generator, config)

        # Should register 3 prompts: 1 base + 2 variants
        assert len(mock_mcp.registered_prompts) == 3

    def test_base_prompt_function_generates_prompt(
        self,
        mock_mcp: Mock,
        mock_generator: Mock,
        mock_config_with_prompts: Mock,
    ) -> None:
        """Test that base prompt function calls composer.compose correctly."""
        mock_generator.composer.compose.return_value = "Generated base prompt"

        register_prompts(mock_mcp, mock_generator, mock_config_with_prompts)

        # Get the registered base prompt function
        research_prompt = mock_mcp.registered_prompts["research"]

        # Call it
        result = research_prompt()

        # Verify it returns the composed prompt
        assert result == "Generated base prompt"

        # Verify composer was called with correct arguments
        mock_generator.composer.compose.assert_called_once()
        call_kwargs = mock_generator.composer.compose.call_args[1]
        assert call_kwargs["action_name"] == "research"
        assert call_kwargs["persona_name"] == "researcher"

    def test_variant_prompt_function_is_async(
        self,
        mock_mcp: Mock,
        mock_generator: Mock,
        mock_config_with_prompts: Mock,
    ) -> None:
        """Test that variant prompt functions are asynchronous."""
        register_prompts(mock_mcp, mock_generator, mock_config_with_prompts)

        # Get the registered variant prompt function
        update_research_prompt = mock_mcp.registered_prompts["update_research"]

        # Verify it's a coroutine function
        import inspect
        assert inspect.iscoroutinefunction(update_research_prompt)

    def test_register_prompts_uses_correct_decorator(
        self,
        mock_mcp: Mock,
        mock_generator: Mock,
        mock_config_with_prompts: Mock,
    ) -> None:
        """Test that register_prompts uses mcp.prompt() decorator."""
        # Track decorator calls
        decorator_calls = []

        def tracking_prompt_decorator():
            def decorator(func):
                decorator_calls.append(func.__name__)
                return func
            return decorator

        mock_mcp.prompt = tracking_prompt_decorator

        register_prompts(mock_mcp, mock_generator, mock_config_with_prompts)

        # Verify prompt decorator was called for each prompt
        assert "research" in decorator_calls
        assert "update_research" in decorator_calls
        assert "refine_research" in decorator_calls

    def test_prompt_function_names_replace_hyphens(
        self,
        mock_mcp: Mock,
        mock_generator: Mock,
        tmp_path: Path,
    ) -> None:
        """Test that prompt function names replace hyphens with underscores."""
        config = Mock()
        config.root = tmp_path / "pareidolia"
        config.generate = Mock()
        config.generate.tool = "copilot"
        config.generate.library = None

        # Create prompt config with action name containing hyphens
        prompt_config = PromptConfig(
            persona="researcher",
            action="deep-research",
            variants=["quick-update"],
            metadata={},
        )

        config.prompt = [prompt_config]

        register_prompts(mock_mcp, mock_generator, config)

        # Function names should use underscores
        assert "deep_research" in mock_mcp.registered_prompts
        assert "quick_update_deep_research" in mock_mcp.registered_prompts

    def test_discover_prompts_handles_empty_metadata(
        self,
        tmp_path: Path,
    ) -> None:
        """Test discover_prompts handles empty metadata dictionaries."""
        config = Mock()
        config.root = tmp_path / "pareidolia"

        prompt_config = PromptConfig(
            persona="researcher",
            action="research",
            variants=["update"],
            metadata={},  # Empty metadata
        )

        config.prompt = [prompt_config]

        prompts = discover_prompts(config)

        assert len(prompts) == 2
        assert prompts[0][4] == {}
        assert prompts[1][4] == {}
