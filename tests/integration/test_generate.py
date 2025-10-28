"""Integration tests for generate functionality."""

from pathlib import Path

from pareidolia.core.config import PareidoliaConfig
from pareidolia.generators.generator import Generator


class TestGenerateIntegration:
    """Integration tests for generate workflow."""

    def test_generate_all_standard_format(self, sample_project: Path) -> None:
        """Test generating all actions in standard format."""
        # Load config
        config_file = sample_project / "pareidolia.toml"
        config = PareidoliaConfig.from_file(config_file)

        # Generate
        generator = Generator(config)
        result = generator.generate_all()

        # Verify results
        assert result.success
        assert len(result.files_generated) == 1
        assert len(result.errors) == 0

        # Check output file
        output_file = sample_project / "prompts" / "research.prompt.md"
        assert output_file.exists()

        content = output_file.read_text()
        assert "expert researcher" in content
        assert "research the following topic" in content

    def test_generate_with_examples(self, sample_project: Path) -> None:
        """Test generating with examples included."""
        config_file = sample_project / "pareidolia.toml"
        config = PareidoliaConfig.from_file(config_file)

        generator = Generator(config)
        result = generator.generate_all(example_names=["report-format"])

        assert result.success

        output_file = sample_project / "prompts" / "research.prompt.md"
        content = output_file.read_text()

        assert "Examples:" in content
        assert "Research Report Example" in content

    def test_generate_with_metadata_in_config(self, tmp_path: Path) -> None:
        """Test generation with metadata in configuration."""
        # Create a minimal project with metadata
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        # Create persona
        persona_dir = project_dir / "pareidolia" / "persona"
        persona_dir.mkdir(parents=True)
        (persona_dir / "researcher.md").write_text("Expert researcher")

        # Create action template that uses metadata
        action_dir = project_dir / "pareidolia" / "action"
        action_dir.mkdir(parents=True)
        action_template = """---
{% if metadata.description %}description: {{ metadata.description }}{% endif %}
{% if metadata.model %}model: {{ metadata.model }}{% endif %}
---

{{ persona }}

Tool: {{ tool }}
Library: {% if library %}{{ library }}{% else %}None{% endif %}
"""
        (action_dir / "analyze.md.j2").write_text(action_template)

        # Create config with metadata
        config_content = """
[pareidolia]
root = "pareidolia"

[generate]
tool = "copilot"
output_dir = "prompts"

[prompts]
persona = "researcher"
action = "analyze"
variants = ["update"]

[prompts.metadata]
description = "Analysis assistant"
model = "claude-3.5-sonnet"
temperature = 0.7
"""
        (project_dir / "pareidolia.toml").write_text(config_content)

        # Load config and generate
        config = PareidoliaConfig.from_file(project_dir / "pareidolia.toml")
        generator = Generator(config)
        result = generator.generate_action("analyze", "researcher")

        assert result.success

        # Check generated file
        output_file = project_dir / "prompts" / "analyze.prompt.md"
        assert output_file.exists()

        content = output_file.read_text()
        assert "description: Analysis assistant" in content
        assert "model: claude-3.5-sonnet" in content
        assert "Tool: copilot" in content
        assert "Library: None" in content

    def test_generate_metadata_accessible_in_templates(self, tmp_path: Path) -> None:
        """Test that metadata variables are accessible in templates."""
        # Create a minimal project
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        # Create persona
        persona_dir = project_dir / "pareidolia" / "persona"
        persona_dir.mkdir(parents=True)
        (persona_dir / "tester.md").write_text("Test persona")

        # Create action template with nested metadata access
        action_dir = project_dir / "pareidolia" / "action"
        action_dir.mkdir(parents=True)
        action_template = """{{ persona }}

Tool: {{ tool }}
{% if metadata.tags %}
Tags: {{ metadata.tags | join(', ') }}
{% endif %}
{% if metadata.settings %}
Model: {{ metadata.settings.model }}
Temp: {{ metadata.settings.temperature }}
{% endif %}
"""
        (action_dir / "test.md.j2").write_text(action_template)

        # Create config with nested metadata
        config_content = """
[pareidolia]
root = "pareidolia"

[generate]
tool = "standard"
output_dir = "prompts"

[prompts]
persona = "tester"
action = "test"
variants = ["refine"]

[prompts.metadata]
tags = ["tag1", "tag2", "tag3"]

[prompts.metadata.settings]
model = "gpt-4"
temperature = 0.8
"""
        (project_dir / "pareidolia.toml").write_text(config_content)

        # Load config and generate
        config = PareidoliaConfig.from_file(project_dir / "pareidolia.toml")
        generator = Generator(config)
        result = generator.generate_action("test", "tester")

        assert result.success

        # Check generated file
        output_file = project_dir / "prompts" / "test.prompt.md"
        content = output_file.read_text()

        assert "Tool: standard" in content
        assert "Tags: tag1, tag2, tag3" in content
        assert "Model: gpt-4" in content
        assert "Temp: 0.8" in content

    def test_generate_copilot_format(self, sample_project: Path) -> None:
        """Test generating in Copilot format."""
        config_file = sample_project / "pareidolia.toml"
        config = PareidoliaConfig.from_file(config_file)

        # Override to use Copilot format
        config = config.merge_overrides(tool="copilot")

        generator = Generator(config)
        result = generator.generate_all()

        assert result.success

        # Standard Copilot format (no library)
        output_file = sample_project / "prompts" / "research.prompt.md"
        assert output_file.exists()

    def test_generate_copilot_library_format(self, sample_project: Path) -> None:
        """Test generating in Copilot library format."""
        config_file = sample_project / "pareidolia.toml"
        config = PareidoliaConfig.from_file(config_file)

        # Override to use Copilot with library
        config = config.merge_overrides(tool="copilot", library="testlib")

        generator = Generator(config)
        result = generator.generate_all()

        assert result.success

        # Copilot library format: flat with prefix
        output_file = sample_project / "prompts" / "testlib.research.prompt.md"
        assert output_file.exists()

    def test_generate_claude_code_library_format(self, sample_project: Path) -> None:
        """Test generating in Claude Code library format."""
        config_file = sample_project / "pareidolia.toml"
        config = PareidoliaConfig.from_file(config_file)

        # Override to use Claude Code with library
        config = config.merge_overrides(tool="claude-code", library="testlib")

        generator = Generator(config)
        result = generator.generate_all()

        assert result.success

        # Claude Code library format: subdirectory
        output_file = sample_project / "prompts" / "testlib" / "research.md"
        assert output_file.exists()

    def test_generate_single_action(self, sample_project: Path) -> None:
        """Test generating a single action."""
        config_file = sample_project / "pareidolia.toml"
        config = PareidoliaConfig.from_file(config_file)

        generator = Generator(config)
        result = generator.generate_action("research", "researcher")

        assert result.success
        assert len(result.files_generated) == 1

        output_file = sample_project / "prompts" / "research.prompt.md"
        assert output_file.exists()

    def test_generate_creates_output_directory(self, sample_project: Path) -> None:
        """Test that generate creates output directory if it doesn't exist."""
        config_file = sample_project / "pareidolia.toml"
        config = PareidoliaConfig.from_file(config_file)

        # Use a non-existent output directory
        config = config.merge_overrides(output_dir="new_output")

        generator = Generator(config)
        result = generator.generate_all()

        assert result.success

        output_dir = sample_project / "new_output"
        assert output_dir.exists()
        assert output_dir.is_dir()

    def test_generate_handles_missing_persona(self, sample_project: Path) -> None:
        """Test that generate handles missing persona gracefully."""
        config_file = sample_project / "pareidolia.toml"
        config = PareidoliaConfig.from_file(config_file)

        generator = Generator(config)
        result = generator.generate_action("research", "nonexistent")

        assert not result.success
        assert len(result.errors) > 0
        assert "nonexistent" in result.errors[0].lower()
