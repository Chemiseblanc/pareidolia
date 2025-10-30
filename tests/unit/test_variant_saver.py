"""Unit tests for variant saver."""

from datetime import datetime
from pathlib import Path

import pytest

from pareidolia.generators.variant_cache import CachedVariant
from pareidolia.generators.variant_saver import VariantSaver


class TestVariantSaver:
    """Tests for VariantSaver class."""

    @pytest.fixture
    def temp_project(self, tmp_path: Path) -> Path:
        """Create a temporary project structure.

        Args:
            tmp_path: Pytest temporary path fixture

        Returns:
            Path to temporary project root
        """
        project_root = tmp_path / "test_project"
        project_root.mkdir()

        # Create pareidolia directory structure
        pareidolia_dir = project_root / "pareidolia"
        pareidolia_dir.mkdir()

        persona_dir = pareidolia_dir / "personas"
        persona_dir.mkdir()

        action_dir = pareidolia_dir / "actions"
        action_dir.mkdir()

        # Create a test persona
        researcher_persona = persona_dir / "researcher.md"
        researcher_persona.write_text(
            "You are an expert researcher specializing in academic analysis."
        )

        return project_root

    @pytest.fixture
    def variant_saver(self, temp_project: Path) -> VariantSaver:
        """Create a VariantSaver instance.

        Args:
            temp_project: Temporary project root

        Returns:
            VariantSaver instance
        """
        return VariantSaver(temp_project)

    @pytest.fixture
    def sample_variant(self) -> CachedVariant:
        """Create a sample cached variant for testing.

        Returns:
            Sample CachedVariant instance
        """
        persona = "You are an expert researcher specializing in academic analysis."
        return CachedVariant(
            variant_name="refine",
            action_name="analyze",
            persona_name="researcher",
            content=f"{persona}\n\nRefine the analysis carefully.",
            generated_at=datetime.now(),
            metadata={"tool": "claude"},
        )

    def test_get_template_path_constructs_correct_path(
        self, variant_saver: VariantSaver, temp_project: Path
    ) -> None:
        """Test that _get_template_path constructs the correct path."""
        expected_path = (
            temp_project
            / "pareidolia"
            / "actions"
            / "refine-analyze.md.j2"
        )
        actual_path = variant_saver._get_template_path("refine", "analyze")

        assert actual_path == expected_path

    def test_get_template_path_different_names(
        self, variant_saver: VariantSaver, temp_project: Path
    ) -> None:
        """Test _get_template_path with different variant and action names."""
        expected_path = (
            temp_project
            / "pareidolia"
            / "actions"
            / "update-research.md.j2"
        )
        actual_path = variant_saver._get_template_path("update", "research")

        assert actual_path == expected_path

    def test_convert_to_template_replaces_persona_content(
        self, variant_saver: VariantSaver
    ) -> None:
        """Test that _convert_to_template replaces persona content correctly."""
        persona_content = "You are an expert researcher."
        variant_content = (
            "You are an expert researcher.\n\nAnalyze the following data carefully."
        )

        result = variant_saver._convert_to_template(variant_content, persona_content)

        assert "{{ persona }}" in result
        assert persona_content not in result
        assert "Analyze the following data carefully." in result

    def test_convert_to_template_preserves_rest_of_content(
        self, variant_saver: VariantSaver
    ) -> None:
        """Test that _convert_to_template preserves content structure."""
        persona_content = "You are a developer."
        variant_content = (
            "You are a developer.\n\n"
            "# Task\n\n"
            "Write clean code.\n\n"
            "# Examples\n\n"
            "Example 1: Good code\n"
            "Example 2: Better code"
        )

        result = variant_saver._convert_to_template(variant_content, persona_content)

        assert "{{ persona }}" in result
        assert "# Task" in result
        assert "# Examples" in result
        assert "Example 1: Good code" in result
        assert "Example 2: Better code" in result

    def test_convert_to_template_handles_persona_not_found(
        self, variant_saver: VariantSaver
    ) -> None:
        """Test _convert_to_template when persona content not in variant."""
        persona_content = "You are a researcher."
        variant_content = "Different content without the persona."

        result = variant_saver._convert_to_template(variant_content, persona_content)

        # Should return content as-is
        assert result == variant_content
        assert "{{ persona }}" not in result

    def test_convert_to_template_handles_already_templated(
        self, variant_saver: VariantSaver
    ) -> None:
        """Test _convert_to_template with already templated content."""
        persona_content = "You are a researcher."
        variant_content = "{{ persona }}\n\nPerform the task."

        result = variant_saver._convert_to_template(variant_content, persona_content)

        # Should return content as-is since persona not found
        assert result == variant_content

    def test_convert_to_template_handles_empty_persona(
        self, variant_saver: VariantSaver
    ) -> None:
        """Test _convert_to_template with empty persona content."""
        persona_content = ""
        variant_content = "Some content here."

        result = variant_saver._convert_to_template(variant_content, persona_content)

        # Empty string would match everything, so should replace
        # But in practice, persona content should never be empty
        assert result == variant_content or "{{ persona }}" in result

    def test_convert_to_template_handles_multiple_occurrences(
        self, variant_saver: VariantSaver
    ) -> None:
        """Test _convert_to_template replaces all occurrences."""
        persona_content = "You are a researcher."
        variant_content = (
            "You are a researcher.\n\n"
            "Remember: You are a researcher.\n\n"
            "Always be: You are a researcher."
        )

        result = variant_saver._convert_to_template(variant_content, persona_content)

        # All occurrences should be replaced
        assert persona_content not in result
        assert result.count("{{ persona }}") == 3

    def test_save_variant_creates_file_when_doesnt_exist(
        self,
        variant_saver: VariantSaver,
        sample_variant: CachedVariant,
        temp_project: Path,
    ) -> None:
        """Test save_variant creates file when it doesn't exist."""
        file_path, was_saved, error_msg = variant_saver.save_variant(sample_variant)

        assert was_saved is True
        assert error_msg is None
        assert file_path.exists()
        expected = temp_project / "pareidolia" / "actions" / "refine-analyze.md.j2"
        assert file_path == expected

        # Verify content
        content = file_path.read_text()
        assert "{{ persona }}" in content
        assert "Refine the analysis carefully." in content

    def test_save_variant_skips_when_exists_force_false(
        self,
        variant_saver: VariantSaver,
        sample_variant: CachedVariant,
        temp_project: Path,
    ) -> None:
        """Test save_variant skips when file exists and force=False."""
        # Create the file first
        action_dir = temp_project / "pareidolia" / "actions"
        action_dir.mkdir(parents=True, exist_ok=True)
        existing_file = action_dir / "refine-analyze.md.j2"
        existing_file.write_text("Existing content")

        file_path, was_saved, error_msg = variant_saver.save_variant(
            sample_variant, force=False
        )

        assert was_saved is False
        assert error_msg == "File exists"
        assert file_path == existing_file

        # Verify original content unchanged
        assert existing_file.read_text() == "Existing content"

    def test_save_variant_overwrites_when_exists_force_true(
        self,
        variant_saver: VariantSaver,
        sample_variant: CachedVariant,
        temp_project: Path,
    ) -> None:
        """Test save_variant overwrites when file exists and force=True."""
        # Create the file first
        action_dir = temp_project / "pareidolia" / "actions"
        action_dir.mkdir(parents=True, exist_ok=True)
        existing_file = action_dir / "refine-analyze.md.j2"
        existing_file.write_text("Existing content")

        file_path, was_saved, error_msg = variant_saver.save_variant(
            sample_variant, force=True
        )

        assert was_saved is True
        assert error_msg is None
        assert file_path == existing_file

        # Verify content was overwritten
        content = existing_file.read_text()
        assert "{{ persona }}" in content
        assert "Existing content" not in content

    def test_save_variant_creates_directories_if_needed(
        self, temp_project: Path, sample_variant: CachedVariant
    ) -> None:
        """Test save_variant creates directories if they don't exist."""
        # Remove action directory
        action_dir = temp_project / "pareidolia" / "actions"
        if action_dir.exists():
            import shutil
            shutil.rmtree(action_dir)

        variant_saver = VariantSaver(temp_project)
        file_path, was_saved, error_msg = variant_saver.save_variant(sample_variant)

        assert was_saved is True
        assert error_msg is None
        assert file_path.exists()
        assert action_dir.exists()

    def test_save_variant_handles_persona_not_found_error(
        self, variant_saver: VariantSaver, temp_project: Path
    ) -> None:
        """Test save_variant handles persona not found error."""
        variant = CachedVariant(
            variant_name="update",
            action_name="research",
            persona_name="nonexistent",
            content="Some content",
            generated_at=datetime.now(),
        )

        file_path, was_saved, error_msg = variant_saver.save_variant(variant)

        assert was_saved is False
        assert error_msg is not None
        assert "Failed to convert template" in error_msg
        assert not file_path.exists()

    def test_save_variant_handles_write_error(
        self,
        variant_saver: VariantSaver,
        sample_variant: CachedVariant,
        temp_project: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test save_variant handles write errors gracefully."""
        # Mock write_file to raise an exception
        def mock_write_file(path: Path, content: str) -> None:
            raise OSError("Simulated write error")

        import pareidolia.generators.variant_saver as saver_module
        monkeypatch.setattr(saver_module, "write_file", mock_write_file)

        file_path, was_saved, error_msg = variant_saver.save_variant(sample_variant)

        assert was_saved is False
        assert error_msg is not None
        assert "Failed to write file" in error_msg

    def test_save_all_processes_multiple_variants(
        self, variant_saver: VariantSaver, temp_project: Path
    ) -> None:
        """Test save_all processes multiple variants correctly."""
        persona = (
            "You are an expert researcher specializing in academic analysis."
        )
        variants = [
            CachedVariant(
                variant_name="refine",
                action_name="analyze",
                persona_name="researcher",
                content=f"{persona}\n\nRefine analysis.",
                generated_at=datetime.now(),
            ),
            CachedVariant(
                variant_name="update",
                action_name="research",
                persona_name="researcher",
                content=f"{persona}\n\nUpdate research.",
                generated_at=datetime.now(),
            ),
            CachedVariant(
                variant_name="summarize",
                action_name="analyze",
                persona_name="researcher",
                content=f"{persona}\n\nSummarize findings.",
                generated_at=datetime.now(),
            ),
        ]

        results = variant_saver.save_all(variants)

        assert len(results) == 3

        # All should succeed
        for _file_path, (was_saved, error_msg) in results.items():
            assert was_saved is True
            assert error_msg is None
            assert _file_path.exists()

    def test_save_all_reports_individual_results(
        self, variant_saver: VariantSaver, temp_project: Path
    ) -> None:
        """Test save_all reports individual results correctly."""
        # Create one existing file
        action_dir = temp_project / "pareidolia" / "actions"
        action_dir.mkdir(parents=True, exist_ok=True)
        existing_file = action_dir / "refine-analyze.md.j2"
        existing_file.write_text("Existing content")

        persona = (
            "You are an expert researcher specializing in academic analysis."
        )
        variants = [
            CachedVariant(
                variant_name="refine",
                action_name="analyze",
                persona_name="researcher",
                content=f"{persona}\n\nRefine analysis.",
                generated_at=datetime.now(),
            ),
            CachedVariant(
                variant_name="update",
                action_name="research",
                persona_name="researcher",
                content=f"{persona}\n\nUpdate research.",
                generated_at=datetime.now(),
            ),
            CachedVariant(
                variant_name="summarize",
                action_name="missing",
                persona_name="nonexistent",
                content="Some content",
                generated_at=datetime.now(),
            ),
        ]

        results = variant_saver.save_all(variants, force=False)

        assert len(results) == 3

        # First should fail (exists)
        refine_path = action_dir / "refine-analyze.md.j2"
        assert results[refine_path] == (False, "File exists")

        # Second should succeed
        update_path = action_dir / "update-research.md.j2"
        assert results[update_path][0] is True
        assert results[update_path][1] is None

        # Third should fail (persona not found)
        summarize_path = action_dir / "summarize-missing.md.j2"
        assert results[summarize_path][0] is False
        assert "Failed to convert template" in results[summarize_path][1]

    def test_save_all_with_force_overwrites_existing(
        self, variant_saver: VariantSaver, temp_project: Path
    ) -> None:
        """Test save_all with force=True overwrites existing files."""
        # Create existing files
        action_dir = temp_project / "pareidolia" / "actions"
        action_dir.mkdir(parents=True, exist_ok=True)
        existing_file1 = action_dir / "refine-analyze.md.j2"
        existing_file1.write_text("Old content 1")
        existing_file2 = action_dir / "update-research.md.j2"
        existing_file2.write_text("Old content 2")

        persona = (
            "You are an expert researcher specializing in academic analysis."
        )
        variants = [
            CachedVariant(
                variant_name="refine",
                action_name="analyze",
                persona_name="researcher",
                content=f"{persona}\n\nNew refine.",
                generated_at=datetime.now(),
            ),
            CachedVariant(
                variant_name="update",
                action_name="research",
                persona_name="researcher",
                content=f"{persona}\n\nNew update.",
                generated_at=datetime.now(),
            ),
        ]

        results = variant_saver.save_all(variants, force=True)

        # All should succeed
        for _file_path, (was_saved, error_msg) in results.items():
            assert was_saved is True
            assert error_msg is None

        # Verify content was overwritten
        assert "{{ persona }}" in existing_file1.read_text()
        assert "Old content 1" not in existing_file1.read_text()
        assert "{{ persona }}" in existing_file2.read_text()
        assert "Old content 2" not in existing_file2.read_text()

    def test_save_all_empty_list(self, variant_saver: VariantSaver) -> None:
        """Test save_all with empty variant list."""
        results = variant_saver.save_all([])

        assert results == {}
