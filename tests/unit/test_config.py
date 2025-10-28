"""Unit tests for configuration management."""

from pathlib import Path

import pytest

from pareidolia.core.config import PareidoliaConfig
from pareidolia.core.exceptions import ConfigurationError


class TestPareidoliaConfigFromDict:
    """Tests for PareidoliaConfig.from_dict method."""

    def test_config_parses_minimal_configuration(self) -> None:
        """Test parsing minimal configuration."""
        config_data = {
            "pareidolia": {"root": "pareidolia"},
            "generate": {"tool": "standard", "output_dir": "prompts"},
        }
        config = PareidoliaConfig.from_dict(config_data, Path("/project"))

        assert config.root == Path("/project/pareidolia")
        assert config.generate.tool == "standard"
        assert config.generate.output_dir == Path("/project/prompts")
        assert config.prompts is None

    def test_config_parses_prompts_section(self) -> None:
        """Test parsing configuration with prompts section."""
        config_data = {
            "pareidolia": {"root": "pareidolia"},
            "generate": {"tool": "standard", "output_dir": "prompts"},
            "prompts": {
                "persona": "researcher",
                "action": "research",
                "variants": ["update", "refine", "summarize"],
                "cli_tool": "claude",
            },
        }
        config = PareidoliaConfig.from_dict(config_data, Path("/project"))

        assert config.prompts is not None
        assert config.prompts.persona == "researcher"
        assert config.prompts.action == "research"
        assert config.prompts.variants == ["update", "refine", "summarize"]
        assert config.prompts.cli_tool == "claude"

    def test_config_handles_missing_prompts_section(self) -> None:
        """Test that prompts section is optional."""
        config_data = {
            "pareidolia": {"root": "pareidolia"},
            "generate": {"tool": "standard", "output_dir": "prompts"},
        }
        config = PareidoliaConfig.from_dict(config_data, Path("/project"))

        assert config.prompts is None

    def test_config_parses_prompts_without_cli_tool(self) -> None:
        """Test parsing prompts without explicit CLI tool."""
        config_data = {
            "pareidolia": {"root": "pareidolia"},
            "generate": {"tool": "standard", "output_dir": "prompts"},
            "prompts": {
                "persona": "researcher",
                "action": "research",
                "variants": ["update"],
            },
        }
        config = PareidoliaConfig.from_dict(config_data, Path("/project"))

        assert config.prompts is not None
        assert config.prompts.cli_tool is None

    def test_config_validates_prompts_required_fields(self) -> None:
        """Test that missing required prompts fields raise error."""
        # Missing persona
        config_data = {
            "pareidolia": {"root": "pareidolia"},
            "generate": {"tool": "standard", "output_dir": "prompts"},
            "prompts": {
                "action": "research",
                "variants": ["update"],
            },
        }
        with pytest.raises(ConfigurationError, match="Invalid prompts"):
            PareidoliaConfig.from_dict(config_data, Path("/project"))

        # Missing action
        config_data = {
            "pareidolia": {"root": "pareidolia"},
            "generate": {"tool": "standard", "output_dir": "prompts"},
            "prompts": {
                "persona": "researcher",
                "variants": ["update"],
            },
        }
        with pytest.raises(ConfigurationError, match="Invalid prompts"):
            PareidoliaConfig.from_dict(config_data, Path("/project"))

        # Missing variants
        config_data = {
            "pareidolia": {"root": "pareidolia"},
            "generate": {"tool": "standard", "output_dir": "prompts"},
            "prompts": {
                "persona": "researcher",
                "action": "research",
            },
        }
        with pytest.raises(ConfigurationError, match="Invalid prompts"):
            PareidoliaConfig.from_dict(config_data, Path("/project"))

    def test_config_handles_invalid_prompts_data(self) -> None:
        """Test that invalid prompts data raises error."""
        # Empty variants list
        config_data = {
            "pareidolia": {"root": "pareidolia"},
            "generate": {"tool": "standard", "output_dir": "prompts"},
            "prompts": {
                "persona": "researcher",
                "action": "research",
                "variants": [],
            },
        }
        with pytest.raises(ConfigurationError, match="Invalid prompts"):
            PareidoliaConfig.from_dict(config_data, Path("/project"))

        # Invalid persona name
        config_data = {
            "pareidolia": {"root": "pareidolia"},
            "generate": {"tool": "standard", "output_dir": "prompts"},
            "prompts": {
                "persona": "Invalid Name",
                "action": "research",
                "variants": ["update"],
            },
        }
        # ValidationError gets wrapped in ConfigurationError by from_dict
        with pytest.raises(ConfigurationError):
            PareidoliaConfig.from_dict(config_data, Path("/project"))

        # Empty CLI tool
        config_data = {
            "pareidolia": {"root": "pareidolia"},
            "generate": {"tool": "standard", "output_dir": "prompts"},
            "prompts": {
                "persona": "researcher",
                "action": "research",
                "variants": ["update"],
                "cli_tool": "",
            },
        }
        with pytest.raises(ConfigurationError, match="Invalid prompts"):
            PareidoliaConfig.from_dict(config_data, Path("/project"))


class TestPareidoliaConfigFromDefaults:
    """Tests for PareidoliaConfig.from_defaults method."""

    def test_from_defaults_creates_config_without_prompts(self) -> None:
        """Test that from_defaults does not include prompts."""
        config = PareidoliaConfig.from_defaults(Path("/project"))

        assert config.root == Path("/project/pareidolia")
        assert config.generate.tool == "standard"
        assert config.prompts is None


class TestPareidoliaConfigMergeOverrides:
    """Tests for PareidoliaConfig.merge_overrides method."""

    def test_merge_overrides_preserves_prompts(self) -> None:
        """Test that merge_overrides preserves prompts configuration."""
        config_data = {
            "pareidolia": {"root": "pareidolia"},
            "generate": {"tool": "standard", "output_dir": "prompts"},
            "prompts": {
                "persona": "researcher",
                "action": "research",
                "variants": ["update"],
            },
        }
        config = PareidoliaConfig.from_dict(config_data, Path("/project"))

        # Apply overrides
        new_config = config.merge_overrides(tool="copilot")

        # Prompts should be preserved
        assert new_config.prompts is not None
        assert new_config.prompts.persona == "researcher"
        assert new_config.prompts.action == "research"
        assert new_config.generate.tool == "copilot"
