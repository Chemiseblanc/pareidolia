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
