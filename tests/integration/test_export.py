"""Integration tests for export functionality."""

from pathlib import Path

from pareidolia.core.config import PareidoliaConfig
from pareidolia.generators.exporter import Exporter


class TestExportIntegration:
    """Integration tests for export workflow."""

    def test_export_all_standard_format(self, sample_project: Path) -> None:
        """Test exporting all actions in standard format."""
        # Load config
        config_file = sample_project / "pareidolia.toml"
        config = PareidoliaConfig.from_file(config_file)

        # Export
        exporter = Exporter(config)
        result = exporter.export_all()

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

    def test_export_with_examples(self, sample_project: Path) -> None:
        """Test exporting with examples included."""
        config_file = sample_project / "pareidolia.toml"
        config = PareidoliaConfig.from_file(config_file)

        exporter = Exporter(config)
        result = exporter.export_all(example_names=["report-format"])

        assert result.success

        output_file = sample_project / "prompts" / "research.prompt.md"
        content = output_file.read_text()

        assert "Examples:" in content
        assert "Research Report Example" in content

    def test_export_copilot_format(self, sample_project: Path) -> None:
        """Test exporting in Copilot format."""
        config_file = sample_project / "pareidolia.toml"
        config = PareidoliaConfig.from_file(config_file)

        # Override to use Copilot format
        config = config.merge_overrides(tool="copilot")

        exporter = Exporter(config)
        result = exporter.export_all()

        assert result.success

        # Standard Copilot format (no library)
        output_file = sample_project / "prompts" / "research.prompt.md"
        assert output_file.exists()

    def test_export_copilot_library_format(self, sample_project: Path) -> None:
        """Test exporting in Copilot library format."""
        config_file = sample_project / "pareidolia.toml"
        config = PareidoliaConfig.from_file(config_file)

        # Override to use Copilot with library
        config = config.merge_overrides(tool="copilot", library="testlib")

        exporter = Exporter(config)
        result = exporter.export_all()

        assert result.success

        # Copilot library format: flat with prefix
        output_file = sample_project / "prompts" / "testlib.research.prompt.md"
        assert output_file.exists()

    def test_export_claude_code_library_format(self, sample_project: Path) -> None:
        """Test exporting in Claude Code library format."""
        config_file = sample_project / "pareidolia.toml"
        config = PareidoliaConfig.from_file(config_file)

        # Override to use Claude Code with library
        config = config.merge_overrides(tool="claude-code", library="testlib")

        exporter = Exporter(config)
        result = exporter.export_all()

        assert result.success

        # Claude Code library format: subdirectory
        output_file = sample_project / "prompts" / "testlib" / "research.md"
        assert output_file.exists()

    def test_export_single_action(self, sample_project: Path) -> None:
        """Test exporting a single action."""
        config_file = sample_project / "pareidolia.toml"
        config = PareidoliaConfig.from_file(config_file)

        exporter = Exporter(config)
        result = exporter.export_action("research", "researcher")

        assert result.success
        assert len(result.files_generated) == 1

        output_file = sample_project / "prompts" / "research.prompt.md"
        assert output_file.exists()

    def test_export_creates_output_directory(self, sample_project: Path) -> None:
        """Test that export creates output directory if it doesn't exist."""
        config_file = sample_project / "pareidolia.toml"
        config = PareidoliaConfig.from_file(config_file)

        # Use a non-existent output directory
        config = config.merge_overrides(output_dir="new_output")

        exporter = Exporter(config)
        result = exporter.export_all()

        assert result.success

        output_dir = sample_project / "new_output"
        assert output_dir.exists()
        assert output_dir.is_dir()

    def test_export_handles_missing_persona(self, sample_project: Path) -> None:
        """Test that export handles missing persona gracefully."""
        config_file = sample_project / "pareidolia.toml"
        config = PareidoliaConfig.from_file(config_file)

        exporter = Exporter(config)
        result = exporter.export_action("research", "nonexistent")

        assert not result.success
        assert len(result.errors) > 0
        assert "nonexistent" in result.errors[0].lower()
