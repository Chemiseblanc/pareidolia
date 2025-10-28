"""Integration tests for frontmatter generation with metadata."""

from pathlib import Path
from typing import Any

from pareidolia.core.models import GenerateConfig
from pareidolia.templates.composer import PromptComposer
from pareidolia.templates.loader import TemplateLoader


class MetadataDict(dict):
    """Mock metadata dictionary that evaluates to True when non-empty."""

    def __bool__(self) -> bool:
        """Return True if dictionary has any items."""
        return len(self) > 0


class MockPromptConfig:
    """Mock PromptConfig for testing metadata access."""

    def __init__(self, metadata: dict[str, Any]) -> None:
        """Initialize with metadata."""
        self.metadata = MetadataDict(metadata)


class TestFrontmatterGeneration:
    """Test frontmatter generation with metadata."""

    def test_frontmatter_with_basic_metadata(self, tmp_path: Path) -> None:
        """Test that frontmatter is generated when metadata is present."""
        # Create test structure
        root = tmp_path / "pareidolia"
        personas_dir = root / "persona"
        actions_dir = root / "action"
        personas_dir.mkdir(parents=True)
        actions_dir.mkdir(parents=True)

        # Create persona
        persona_file = personas_dir / "researcher.md"
        persona_file.write_text("You are an expert researcher.")

        # Create action with frontmatter template
        action_file = actions_dir / "analyze.md.j2"
        action_content = """\
{%- if metadata -%}
---
{%- if metadata.description %}
description: {{ metadata.description }}
{%- endif %}
{%- if metadata.model %}
model: {{ metadata.model }}
{%- endif %}
---

{% endif -%}
# Analysis Task

{{ persona }}

Perform analysis.
"""
        action_file.write_text(action_content)

        # Create config with metadata
        metadata = {
            "description": "Research analysis assistant",
            "model": "claude-3.5-sonnet",
        }
        prompt_config = MockPromptConfig(metadata)
        generate_config = GenerateConfig(
            tool="standard", library=None, output_dir=tmp_path / "output"
        )

        # Generate prompt
        loader = TemplateLoader(root)
        composer = PromptComposer(loader, generate_config=generate_config)
        result = composer.compose(
            action_name="analyze",
            persona_name="researcher",
            prompt_config=prompt_config,
        )

        # Verify frontmatter is present
        assert result.startswith("---\n")
        assert "description: Research analysis assistant" in result
        assert "model: claude-3.5-sonnet" in result
        assert "# Analysis Task" in result
        assert "You are an expert researcher." in result

    def test_no_frontmatter_without_metadata(self, tmp_path: Path) -> None:
        """Test that no frontmatter is generated when metadata is absent."""
        # Create test structure
        root = tmp_path / "pareidolia"
        personas_dir = root / "persona"
        actions_dir = root / "action"
        personas_dir.mkdir(parents=True)
        actions_dir.mkdir(parents=True)

        # Create persona
        persona_file = personas_dir / "researcher.md"
        persona_file.write_text("You are an expert researcher.")

        # Create action with conditional frontmatter
        action_file = actions_dir / "analyze.md.j2"
        action_content = """\
{%- if metadata -%}
---
{%- if metadata.description %}
description: {{ metadata.description }}
{%- endif %}
---

{% endif -%}
# Analysis Task

{{ persona }}

Perform analysis.
"""
        action_file.write_text(action_content)

        # Create config without metadata (empty dict)
        prompt_config = MockPromptConfig({})
        generate_config = GenerateConfig(
            tool="standard", library=None, output_dir=tmp_path / "output"
        )

        # Generate prompt
        loader = TemplateLoader(root)
        composer = PromptComposer(loader, generate_config=generate_config)
        result = composer.compose(
            action_name="analyze",
            persona_name="researcher",
            prompt_config=prompt_config,
        )

        # Verify no frontmatter
        assert not result.startswith("---")
        assert result.startswith("# Analysis Task")

    def test_frontmatter_with_tool_and_library(self, tmp_path: Path) -> None:
        """Test that tool and library information is available in frontmatter."""
        # Create test structure
        root = tmp_path / "pareidolia"
        personas_dir = root / "persona"
        actions_dir = root / "action"
        personas_dir.mkdir(parents=True)
        actions_dir.mkdir(parents=True)

        # Create persona
        persona_file = personas_dir / "researcher.md"
        persona_file.write_text("You are an expert researcher.")

        # Create action with tool/library frontmatter
        action_file = actions_dir / "analyze.md.j2"
        action_content = """\
{%- if metadata -%}
---
{%- if tool %}
tool: {{ tool }}
{%- endif %}
{%- if library %}
library: {{ library }}
{%- endif %}
{%- if metadata.description %}
description: {{ metadata.description }}
{%- endif %}
---

{% endif -%}
# Analysis Task

{{ persona }}
"""
        action_file.write_text(action_content)

        # Create config with metadata
        metadata = {"description": "Test prompt"}
        prompt_config = MockPromptConfig(metadata)
        generate_config = GenerateConfig(
            tool="copilot", library="mylib", output_dir=tmp_path / "output"
        )

        # Generate prompt
        loader = TemplateLoader(root)
        composer = PromptComposer(loader, generate_config=generate_config)
        result = composer.compose(
            action_name="analyze",
            persona_name="researcher",
            prompt_config=prompt_config,
        )

        # Verify frontmatter includes tool and library
        assert "tool: copilot" in result
        assert "library: mylib" in result
        assert "description: Test prompt" in result

    def test_frontmatter_with_nested_metadata(self, tmp_path: Path) -> None:
        """Test frontmatter generation with nested metadata structures."""
        # Create test structure
        root = tmp_path / "pareidolia"
        personas_dir = root / "persona"
        actions_dir = root / "action"
        personas_dir.mkdir(parents=True)
        actions_dir.mkdir(parents=True)

        # Create persona
        persona_file = personas_dir / "researcher.md"
        persona_file.write_text("You are an expert researcher.")

        # Create action with nested metadata access
        action_file = actions_dir / "analyze.md.j2"
        action_content = """\
{%- if metadata -%}
---
{%- if metadata.config %}
config:
{%- if metadata.config.model %}
  model: {{ metadata.config.model }}
{%- endif %}
{%- if metadata.config.temperature %}
  temperature: {{ metadata.config.temperature }}
{%- endif %}
{%- endif %}
---

{% endif -%}
# Analysis Task

{{ persona }}
"""
        action_file.write_text(action_content)

        # Create config with nested metadata
        metadata = {
            "config": {
                "model": "claude-3.5-sonnet",
                "temperature": 0.7,
            }
        }
        prompt_config = MockPromptConfig(metadata)
        generate_config = GenerateConfig(
            tool="standard", library=None, output_dir=tmp_path / "output"
        )

        # Generate prompt
        loader = TemplateLoader(root)
        composer = PromptComposer(loader, generate_config=generate_config)
        result = composer.compose(
            action_name="analyze",
            persona_name="researcher",
            prompt_config=prompt_config,
        )

        # Verify nested metadata in frontmatter
        assert "config:" in result
        assert "  model: claude-3.5-sonnet" in result
        assert "  temperature: 0.7" in result

    def test_frontmatter_with_tags_array(self, tmp_path: Path) -> None:
        """Test frontmatter generation with array metadata (tags)."""
        # Create test structure
        root = tmp_path / "pareidolia"
        personas_dir = root / "persona"
        actions_dir = root / "action"
        personas_dir.mkdir(parents=True)
        actions_dir.mkdir(parents=True)

        # Create persona
        persona_file = personas_dir / "researcher.md"
        persona_file.write_text("You are an expert researcher.")

        # Create action with tags in frontmatter
        action_file = actions_dir / "analyze.md.j2"
        action_content = """\
{%- if metadata -%}
---
{%- if metadata.tags %}
tags: {{ metadata.tags | tojson }}
{%- endif %}
---

{% endif -%}
# Analysis Task

{{ persona }}
"""
        action_file.write_text(action_content)

        # Create config with tags metadata
        metadata = {"tags": ["analysis", "research", "report"]}
        prompt_config = MockPromptConfig(metadata)
        generate_config = GenerateConfig(
            tool="standard", library=None, output_dir=tmp_path / "output"
        )

        # Generate prompt
        loader = TemplateLoader(root)
        composer = PromptComposer(loader, generate_config=generate_config)
        result = composer.compose(
            action_name="analyze",
            persona_name="researcher",
            prompt_config=prompt_config,
        )

        # Verify tags in frontmatter as JSON array
        assert 'tags: ["analysis", "research", "report"]' in result

    def test_frontmatter_copilot_style(self, tmp_path: Path) -> None:
        """Test GitHub Copilot-style frontmatter generation."""
        # Create test structure
        root = tmp_path / "pareidolia"
        personas_dir = root / "persona"
        actions_dir = root / "action"
        personas_dir.mkdir(parents=True)
        actions_dir.mkdir(parents=True)

        # Create persona
        persona_file = personas_dir / "coder.md"
        persona_file.write_text("You are an expert coder.")

        # Create action with Copilot-style frontmatter
        action_file = actions_dir / "review.md.j2"
        action_content = """\
{%- if metadata -%}
---
{%- if metadata.description %}
description: {{ metadata.description }}
{%- endif %}
{%- if metadata.tags %}
tags: {{ metadata.tags | tojson }}
{%- endif %}
---

{% endif -%}
# Code Review

{{ persona }}

Review the following code.
"""
        action_file.write_text(action_content)

        # Create config with Copilot metadata
        metadata = {
            "description": "Code review assistant",
            "tags": ["code-review", "best-practices"],
        }
        prompt_config = MockPromptConfig(metadata)
        generate_config = GenerateConfig(
            tool="copilot", library=None, output_dir=tmp_path / "output"
        )

        # Generate prompt
        loader = TemplateLoader(root)
        composer = PromptComposer(loader, generate_config=generate_config)
        result = composer.compose(
            action_name="review",
            persona_name="coder",
            prompt_config=prompt_config,
        )

        # Verify Copilot-style frontmatter
        assert "description: Code review assistant" in result
        assert 'tags: ["code-review", "best-practices"]' in result

    def test_frontmatter_claude_style(self, tmp_path: Path) -> None:
        """Test Claude Code-style frontmatter generation."""
        # Create test structure
        root = tmp_path / "pareidolia"
        personas_dir = root / "persona"
        actions_dir = root / "action"
        personas_dir.mkdir(parents=True)
        actions_dir.mkdir(parents=True)

        # Create persona
        persona_file = personas_dir / "researcher.md"
        persona_file.write_text("You are an expert researcher.")

        # Create action with Claude-style frontmatter
        action_file = actions_dir / "analyze.md.j2"
        action_content = """\
{%- if metadata -%}
---
{%- if metadata.description %}
description: {{ metadata.description }}
{%- endif %}
{%- if metadata.model %}
model: {{ metadata.model }}
{%- endif %}
{%- if metadata.chat_mode %}
chat_mode: {{ metadata.chat_mode }}
{%- endif %}
{%- if metadata.temperature %}
temperature: {{ metadata.temperature }}
{%- endif %}
---

{% endif -%}
# Analysis Task

{{ persona }}
"""
        action_file.write_text(action_content)

        # Create config with Claude metadata
        metadata = {
            "description": "Research analysis assistant",
            "model": "claude-3.5-sonnet",
            "chat_mode": "extended",
            "temperature": 0.7,
        }
        prompt_config = MockPromptConfig(metadata)
        generate_config = GenerateConfig(
            tool="claude-code", library=None, output_dir=tmp_path / "output"
        )

        # Generate prompt
        loader = TemplateLoader(root)
        composer = PromptComposer(loader, generate_config=generate_config)
        result = composer.compose(
            action_name="analyze",
            persona_name="researcher",
            prompt_config=prompt_config,
        )

        # Verify Claude-style frontmatter
        assert "description: Research analysis assistant" in result
        assert "model: claude-3.5-sonnet" in result
        assert "chat_mode: extended" in result
        assert "temperature: 0.7" in result

    def test_backward_compatibility_no_metadata(
        self, tmp_path: Path
    ) -> None:
        """Test backward compatibility when no metadata is configured."""
        # Create test structure
        root = tmp_path / "pareidolia"
        personas_dir = root / "persona"
        actions_dir = root / "action"
        personas_dir.mkdir(parents=True)
        actions_dir.mkdir(parents=True)

        # Create persona
        persona_file = personas_dir / "researcher.md"
        persona_file.write_text("You are an expert researcher.")

        # Create simple action without metadata support
        action_file = actions_dir / "analyze.md.j2"
        action_content = """\
# Analysis Task

{{ persona }}

Perform analysis.
"""
        action_file.write_text(action_content)

        # Create config without metadata
        generate_config = GenerateConfig(
            tool="standard", library=None, output_dir=tmp_path / "output"
        )

        # Generate prompt without prompt_config
        loader = TemplateLoader(root)
        composer = PromptComposer(loader, generate_config=generate_config)
        result = composer.compose(
            action_name="analyze",
            persona_name="researcher",
            # No prompt_config provided
        )

        # Verify simple generation works
        assert result.startswith("# Analysis Task")
        assert "You are an expert researcher." in result
        assert "---" not in result  # No frontmatter

