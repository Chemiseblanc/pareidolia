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
            "export": {"tool": "standard", "output_dir": "prompts"},
        }
        config = PareidoliaConfig.from_dict(config_data, Path("/project"))

        assert config.root == Path("/project/pareidolia")
        assert config.export.tool == "standard"
        assert config.export.output_dir == Path("/project/prompts")
        assert config.variants is None

    def test_config_parses_variants_section(self) -> None:
        """Test parsing configuration with variants section."""
        config_data = {
            "pareidolia": {"root": "pareidolia"},
            "export": {"tool": "standard", "output_dir": "prompts"},
            "variants": {
                "persona": "researcher",
                "action": "research",
                "generate": ["update", "refine", "summarize"],
                "cli_tool": "claude",
            },
        }
        config = PareidoliaConfig.from_dict(config_data, Path("/project"))

        assert config.variants is not None
        assert config.variants.persona == "researcher"
        assert config.variants.action == "research"
        assert config.variants.generate == ["update", "refine", "summarize"]
        assert config.variants.cli_tool == "claude"

    def test_config_handles_missing_variants_section(self) -> None:
        """Test that variants section is optional."""
        config_data = {
            "pareidolia": {"root": "pareidolia"},
            "export": {"tool": "standard", "output_dir": "prompts"},
        }
        config = PareidoliaConfig.from_dict(config_data, Path("/project"))

        assert config.variants is None

    def test_config_parses_variants_without_cli_tool(self) -> None:
        """Test parsing variants without explicit CLI tool."""
        config_data = {
            "pareidolia": {"root": "pareidolia"},
            "export": {"tool": "standard", "output_dir": "prompts"},
            "variants": {
                "persona": "researcher",
                "action": "research",
                "generate": ["update"],
            },
        }
        config = PareidoliaConfig.from_dict(config_data, Path("/project"))

        assert config.variants is not None
        assert config.variants.cli_tool is None

    def test_config_validates_variants_required_fields(self) -> None:
        """Test that missing required variant fields raise error."""
        # Missing persona
        config_data = {
            "pareidolia": {"root": "pareidolia"},
            "export": {"tool": "standard", "output_dir": "prompts"},
            "variants": {
                "action": "research",
                "generate": ["update"],
            },
        }
        with pytest.raises(ConfigurationError, match="Invalid variants"):
            PareidoliaConfig.from_dict(config_data, Path("/project"))

        # Missing action
        config_data = {
            "pareidolia": {"root": "pareidolia"},
            "export": {"tool": "standard", "output_dir": "prompts"},
            "variants": {
                "persona": "researcher",
                "generate": ["update"],
            },
        }
        with pytest.raises(ConfigurationError, match="Invalid variants"):
            PareidoliaConfig.from_dict(config_data, Path("/project"))

        # Missing generate
        config_data = {
            "pareidolia": {"root": "pareidolia"},
            "export": {"tool": "standard", "output_dir": "prompts"},
            "variants": {
                "persona": "researcher",
                "action": "research",
            },
        }
        with pytest.raises(ConfigurationError, match="Invalid variants"):
            PareidoliaConfig.from_dict(config_data, Path("/project"))

    def test_config_handles_invalid_variants_data(self) -> None:
        """Test that invalid variant data raises error."""
        # Empty generate list
        config_data = {
            "pareidolia": {"root": "pareidolia"},
            "export": {"tool": "standard", "output_dir": "prompts"},
            "variants": {
                "persona": "researcher",
                "action": "research",
                "generate": [],
            },
        }
        with pytest.raises(ConfigurationError, match="Invalid variants"):
            PareidoliaConfig.from_dict(config_data, Path("/project"))

        # Invalid persona name
        config_data = {
            "pareidolia": {"root": "pareidolia"},
            "export": {"tool": "standard", "output_dir": "prompts"},
            "variants": {
                "persona": "Invalid Name",
                "action": "research",
                "generate": ["update"],
            },
        }
        # ValidationError gets wrapped in ConfigurationError by from_dict
        with pytest.raises(ConfigurationError):
            PareidoliaConfig.from_dict(config_data, Path("/project"))

        # Empty CLI tool
        config_data = {
            "pareidolia": {"root": "pareidolia"},
            "export": {"tool": "standard", "output_dir": "prompts"},
            "variants": {
                "persona": "researcher",
                "action": "research",
                "generate": ["update"],
                "cli_tool": "",
            },
        }
        with pytest.raises(ConfigurationError, match="Invalid variants"):
            PareidoliaConfig.from_dict(config_data, Path("/project"))


class TestPareidoliaConfigFromDefaults:
    """Tests for PareidoliaConfig.from_defaults method."""

    def test_from_defaults_creates_config_without_variants(self) -> None:
        """Test that from_defaults does not include variants."""
        config = PareidoliaConfig.from_defaults(Path("/project"))

        assert config.root == Path("/project/pareidolia")
        assert config.export.tool == "standard"
        assert config.variants is None


class TestPareidoliaConfigMergeOverrides:
    """Tests for PareidoliaConfig.merge_overrides method."""

    def test_merge_overrides_preserves_variants(self) -> None:
        """Test that merge_overrides preserves variants configuration."""
        config_data = {
            "pareidolia": {"root": "pareidolia"},
            "export": {"tool": "standard", "output_dir": "prompts"},
            "variants": {
                "persona": "researcher",
                "action": "research",
                "generate": ["update"],
            },
        }
        config = PareidoliaConfig.from_dict(config_data, Path("/project"))

        # Apply overrides
        new_config = config.merge_overrides(tool="copilot")

        # Variants should be preserved
        assert new_config.variants is not None
        assert new_config.variants.persona == "researcher"
        assert new_config.variants.action == "research"
        assert new_config.export.tool == "copilot"
