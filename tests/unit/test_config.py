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
        assert config.metadata == {}
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


class TestPareidoliaConfigMetadata:
    """Tests for metadata support in configuration."""

    def test_config_parses_metadata_section(self) -> None:
        """Test parsing configuration with prompts.metadata section."""
        config_data = {
            "pareidolia": {"root": "pareidolia"},
            "generate": {"tool": "standard", "output_dir": "prompts"},
            "prompts": {
                "persona": "researcher",
                "action": "research",
                "variants": ["update"],
                "metadata": {
                    "description": "Research assistant",
                    "model": "claude-3.5-sonnet",
                    "temperature": 0.7,
                },
            },
        }
        config = PareidoliaConfig.from_dict(config_data, Path("/project"))

        assert config.prompts is not None
        assert config.prompts.metadata is not None
        assert config.prompts.metadata["description"] == "Research assistant"
        assert config.prompts.metadata["model"] == "claude-3.5-sonnet"
        assert config.prompts.metadata["temperature"] == 0.7

    def test_config_handles_missing_metadata_section(self) -> None:
        """Test that metadata section is optional and defaults to empty dict."""
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
        assert config.prompts.metadata == {}

    def test_config_parses_metadata_with_various_types(self) -> None:
        """Test that metadata can contain various data types."""
        config_data = {
            "pareidolia": {"root": "pareidolia"},
            "generate": {"tool": "standard", "output_dir": "prompts"},
            "prompts": {
                "persona": "researcher",
                "action": "research",
                "variants": ["update"],
                "metadata": {
                    "description": "Test",
                    "chat_mode": "extended",
                    "temperature": 0.7,
                    "max_tokens": 4096,
                    "tags": ["analysis", "research"],
                    "enabled": True,
                },
            },
        }
        config = PareidoliaConfig.from_dict(config_data, Path("/project"))

        assert config.prompts is not None
        metadata = config.prompts.metadata
        assert isinstance(metadata["description"], str)
        assert isinstance(metadata["temperature"], float)
        assert isinstance(metadata["max_tokens"], int)
        assert isinstance(metadata["tags"], list)
        assert isinstance(metadata["enabled"], bool)

    def test_config_parses_nested_metadata(self) -> None:
        """Test parsing configuration with nested metadata structures."""
        config_data = {
            "pareidolia": {"root": "pareidolia"},
            "generate": {"tool": "standard", "output_dir": "prompts"},
            "prompts": {
                "persona": "researcher",
                "action": "research",
                "variants": ["update"],
                "metadata": {
                    "description": "Nested test",
                    "settings": {
                        "model": "claude-3.5-sonnet",
                        "temperature": 0.7,
                        "parameters": {
                            "max_tokens": 4096,
                            "top_p": 0.9,
                        },
                    },
                    "tags": ["tag1", "tag2"],
                },
            },
        }
        config = PareidoliaConfig.from_dict(config_data, Path("/project"))

        assert config.prompts is not None
        metadata = config.prompts.metadata
        assert metadata["settings"]["model"] == "claude-3.5-sonnet"
        assert metadata["settings"]["parameters"]["max_tokens"] == 4096
        assert metadata["tags"] == ["tag1", "tag2"]

    def test_config_metadata_flows_to_prompt_config(self) -> None:
        """Test that metadata flows correctly from config to PromptConfig."""
        config_data = {
            "pareidolia": {"root": "pareidolia"},
            "generate": {"tool": "copilot", "output_dir": "prompts"},
            "prompts": {
                "persona": "researcher",
                "action": "analyze",
                "variants": ["expand", "refine"],
                "cli_tool": "claude",
                "metadata": {
                    "description": "Analysis tool",
                    "model": "claude-3.5-sonnet",
                },
            },
        }
        config = PareidoliaConfig.from_dict(config_data, Path("/project"))

        assert config.prompts is not None
        assert config.prompts.persona == "researcher"
        assert config.prompts.action == "analyze"
        assert config.prompts.variants == ["expand", "refine"]
        assert config.prompts.cli_tool == "claude"
        assert config.prompts.metadata["description"] == "Analysis tool"
        assert config.prompts.metadata["model"] == "claude-3.5-sonnet"

    def test_config_empty_metadata_section(self) -> None:
        """Test that empty metadata section results in empty dict."""
        config_data = {
            "pareidolia": {"root": "pareidolia"},
            "generate": {"tool": "standard", "output_dir": "prompts"},
            "prompts": {
                "persona": "researcher",
                "action": "research",
                "variants": ["update"],
                "metadata": {},
            },
        }
        config = PareidoliaConfig.from_dict(config_data, Path("/project"))

        assert config.prompts is not None
        assert config.prompts.metadata == {}

    def test_config_backward_compatibility_without_metadata(self) -> None:
        """Test backward compatibility with configs that don't have metadata."""
        # Old-style config without metadata
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
        assert config.prompts.metadata == {}
        assert isinstance(config.prompts.metadata, dict)


class TestPareidoliaConfigGlobalMetadata:
    """Tests for global metadata support in configuration."""

    def test_config_parses_global_metadata_section(self) -> None:
        """Test parsing configuration with global [metadata] section."""
        config_data = {
            "pareidolia": {"root": "pareidolia"},
            "generate": {"tool": "standard", "output_dir": "prompts"},
            "metadata": {
                "model": "claude-3.5-sonnet",
                "temperature": 0.7,
                "tags": ["default", "global"],
            },
        }
        config = PareidoliaConfig.from_dict(config_data, Path("/project"))

        assert config.metadata is not None
        assert config.metadata["model"] == "claude-3.5-sonnet"
        assert config.metadata["temperature"] == 0.7
        assert config.metadata["tags"] == ["default", "global"]

    def test_config_handles_missing_global_metadata_section(self) -> None:
        """Test that global metadata section is optional and defaults to empty dict."""
        config_data = {
            "pareidolia": {"root": "pareidolia"},
            "generate": {"tool": "standard", "output_dir": "prompts"},
        }
        config = PareidoliaConfig.from_dict(config_data, Path("/project"))

        assert config.metadata == {}
        assert isinstance(config.metadata, dict)

    def test_config_merges_global_and_prompt_metadata(self) -> None:
        """Test that global and per-prompt metadata are merged correctly."""
        config_data = {
            "pareidolia": {"root": "pareidolia"},
            "generate": {"tool": "standard", "output_dir": "prompts"},
            "metadata": {
                "model": "claude-3.5-sonnet",
                "temperature": 0.7,
                "mode": "default",
            },
            "prompts": {
                "persona": "researcher",
                "action": "analyze",
                "variants": ["update"],
                "metadata": {
                    "mode": "agent",  # Override global
                    "description": "Conducts and reports research findings",
                },
            },
        }
        config = PareidoliaConfig.from_dict(config_data, Path("/project"))

        # Global metadata should be accessible
        assert config.metadata["model"] == "claude-3.5-sonnet"
        assert config.metadata["temperature"] == 0.7
        assert config.metadata["mode"] == "default"

        # Prompt metadata should have merged values
        assert config.prompts is not None
        assert config.prompts.metadata["model"] == "claude-3.5-sonnet"  # From global
        assert config.prompts.metadata["temperature"] == 0.7  # From global
        assert config.prompts.metadata["mode"] == "agent"  # Override from prompt
        assert (
            config.prompts.metadata["description"]
            == "Conducts and reports research findings"
        )  # From prompt

    def test_config_prompt_metadata_overrides_global(self) -> None:
        """Test that per-prompt metadata overrides global metadata."""
        config_data = {
            "pareidolia": {"root": "pareidolia"},
            "generate": {"tool": "standard", "output_dir": "prompts"},
            "metadata": {
                "model": "claude-3.5-sonnet",
                "description": "Default description",
                "temperature": 0.5,
            },
            "prompts": {
                "persona": "researcher",
                "action": "research",
                "variants": ["update"],
                "metadata": {
                    "model": "Claude Sonnet 4",  # Override
                    "description": "Conducts and reports research findings",  # Override
                },
            },
        }
        config = PareidoliaConfig.from_dict(config_data, Path("/project"))

        assert config.prompts is not None
        assert config.prompts.metadata["model"] == "Claude Sonnet 4"
        assert (
            config.prompts.metadata["description"]
            == "Conducts and reports research findings"
        )
        assert config.prompts.metadata["temperature"] == 0.5  # From global

    def test_config_only_global_metadata_no_prompt_metadata(self) -> None:
        """Test configuration with only global metadata, no per-prompt metadata."""
        config_data = {
            "pareidolia": {"root": "pareidolia"},
            "generate": {"tool": "standard", "output_dir": "prompts"},
            "metadata": {
                "model": "claude-3.5-sonnet",
                "temperature": 0.7,
            },
            "prompts": {
                "persona": "researcher",
                "action": "research",
                "variants": ["update"],
                # No metadata key
            },
        }
        config = PareidoliaConfig.from_dict(config_data, Path("/project"))

        # Global metadata is set
        assert config.metadata["model"] == "claude-3.5-sonnet"
        assert config.metadata["temperature"] == 0.7

        # Prompt should inherit global metadata
        assert config.prompts is not None
        assert config.prompts.metadata["model"] == "claude-3.5-sonnet"
        assert config.prompts.metadata["temperature"] == 0.7

    def test_config_only_prompt_metadata_no_global_metadata(self) -> None:
        """Test configuration with only per-prompt metadata, no global metadata."""
        config_data = {
            "pareidolia": {"root": "pareidolia"},
            "generate": {"tool": "standard", "output_dir": "prompts"},
            # No metadata section
            "prompts": {
                "persona": "researcher",
                "action": "research",
                "variants": ["update"],
                "metadata": {
                    "mode": "agent",
                    "description": "Research prompt",
                },
            },
        }
        config = PareidoliaConfig.from_dict(config_data, Path("/project"))

        # Global metadata should be empty
        assert config.metadata == {}

        # Prompt metadata should only contain prompt-specific values
        assert config.prompts is not None
        assert config.prompts.metadata["mode"] == "agent"
        assert config.prompts.metadata["description"] == "Research prompt"
        assert len(config.prompts.metadata) == 2

    def test_config_global_metadata_with_nested_structures(self) -> None:
        """Test global metadata with nested dictionaries and arrays."""
        config_data = {
            "pareidolia": {"root": "pareidolia"},
            "generate": {"tool": "standard", "output_dir": "prompts"},
            "metadata": {
                "model": "claude-3.5-sonnet",
                "settings": {
                    "temperature": 0.7,
                    "max_tokens": 4096,
                },
                "tags": ["global", "default"],
            },
            "prompts": {
                "persona": "researcher",
                "action": "research",
                "variants": ["update"],
                "metadata": {
                    "description": "Specific prompt",
                },
            },
        }
        config = PareidoliaConfig.from_dict(config_data, Path("/project"))

        assert config.prompts is not None
        # Global nested structures should be inherited
        assert config.prompts.metadata["model"] == "claude-3.5-sonnet"
        assert config.prompts.metadata["settings"]["temperature"] == 0.7
        assert config.prompts.metadata["settings"]["max_tokens"] == 4096
        assert config.prompts.metadata["tags"] == ["global", "default"]
        # Prompt-specific metadata should be present
        assert config.prompts.metadata["description"] == "Specific prompt"

    def test_config_invalid_global_metadata_type(self) -> None:
        """Test that invalid global metadata type raises error."""
        config_data = {
            "pareidolia": {"root": "pareidolia"},
            "generate": {"tool": "standard", "output_dir": "prompts"},
            "metadata": "not a dictionary",  # Invalid type
        }
        with pytest.raises(ConfigurationError, match="metadata section must be"):
            PareidoliaConfig.from_dict(config_data, Path("/project"))

    def test_config_empty_global_metadata_section(self) -> None:
        """Test that empty global metadata section results in empty dict."""
        config_data = {
            "pareidolia": {"root": "pareidolia"},
            "generate": {"tool": "standard", "output_dir": "prompts"},
            "metadata": {},
        }
        config = PareidoliaConfig.from_dict(config_data, Path("/project"))

        assert config.metadata == {}
        assert isinstance(config.metadata, dict)


class TestPareidoliaConfigFromDefaults:
    """Tests for PareidoliaConfig.from_defaults method."""

    def test_from_defaults_creates_config_without_prompts(self) -> None:
        """Test that from_defaults does not include prompts."""
        config = PareidoliaConfig.from_defaults(Path("/project"))

        assert config.root == Path("/project/pareidolia")
        assert config.generate.tool == "standard"
        assert config.metadata == {}
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

    def test_merge_overrides_preserves_metadata(self) -> None:
        """Test that merge_overrides preserves metadata in prompts."""
        config_data = {
            "pareidolia": {"root": "pareidolia"},
            "generate": {"tool": "standard", "output_dir": "prompts"},
            "prompts": {
                "persona": "researcher",
                "action": "research",
                "variants": ["update"],
                "metadata": {
                    "description": "Test prompt",
                    "model": "claude-3.5-sonnet",
                },
            },
        }
        config = PareidoliaConfig.from_dict(config_data, Path("/project"))

        # Apply overrides
        new_config = config.merge_overrides(tool="copilot")

        # Metadata should be preserved
        assert new_config.prompts is not None
        assert new_config.prompts.metadata["description"] == "Test prompt"
        assert new_config.prompts.metadata["model"] == "claude-3.5-sonnet"
