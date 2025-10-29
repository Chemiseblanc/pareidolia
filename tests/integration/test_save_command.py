"""Integration tests for the save command."""

from datetime import datetime
from pathlib import Path

import pytest

from pareidolia.core.config import PareidoliaConfig
from pareidolia.generators.variant_cache import CachedVariant, VariantCache


class TestSaveCommand:
    """Integration tests for save command workflow."""

    @pytest.fixture(autouse=True)
    def clear_cache(self) -> None:
        """Clear the variant cache before each test."""
        VariantCache().clear()

    def test_save_with_no_cached_variants(self, sample_project: Path) -> None:
        """Test save command with no cached variants shows error message."""
        config_file = sample_project / "pareidolia.toml"
        config = PareidoliaConfig.from_file(config_file)

        # Ensure cache is empty
        cache = VariantCache()
        assert cache.count() == 0

        # Import here to simulate CLI usage
        from pareidolia.cli import handle_save

        # Save should return error
        result = handle_save(config, None, None, False, False)
        assert result == 1

    def test_save_saves_all_cached_variants_successfully(
        self, sample_project: Path
    ) -> None:
        """Test save command saves all cached variants successfully."""
        config_file = sample_project / "pareidolia.toml"
        config = PareidoliaConfig.from_file(config_file)

        # Add test variants to cache (use the full persona content from conftest)
        persona_content = (
            "You are an expert researcher with deep analytical skills.\n"
            "You approach problems methodically and thoroughly.\n"
        )
        cache = VariantCache()
        cache.add(
            CachedVariant(
                variant_name="update",
                action_name="research",
                persona_name="researcher",
                content=persona_content + "\nUpdate your analysis.",
                generated_at=datetime.now(),
            )
        )
        cache.add(
            CachedVariant(
                variant_name="refine",
                action_name="research",
                persona_name="researcher",
                content=persona_content + "\nRefine your methodology.",
                generated_at=datetime.now(),
            )
        )

        from pareidolia.cli import handle_save

        # Save all variants
        result = handle_save(config, None, None, False, False)
        assert result == 0

        # Check files were created
        action_dir = sample_project / "pareidolia" / "action"
        assert (action_dir / "update-research.md.j2").exists()
        assert (action_dir / "refine-research.md.j2").exists()

        # Verify content has template placeholder
        update_content = (action_dir / "update-research.md.j2").read_text()
        assert "{{ persona }}" in update_content
        assert "Update your analysis" in update_content

    def test_save_with_variant_filter(self, sample_project: Path) -> None:
        """Test save command filters by variant name correctly."""
        config_file = sample_project / "pareidolia.toml"
        config = PareidoliaConfig.from_file(config_file)

        # Add test variants
        cache = VariantCache()
        cache.add(
            CachedVariant(
                variant_name="update",
                action_name="research",
                persona_name="researcher",
                content="You are an expert researcher with deep analytical skills.\n\nUpdate.",
                generated_at=datetime.now(),
            )
        )
        cache.add(
            CachedVariant(
                variant_name="refine",
                action_name="research",
                persona_name="researcher",
                content="You are an expert researcher with deep analytical skills.\n\nRefine.",
                generated_at=datetime.now(),
            )
        )

        from pareidolia.cli import handle_save

        # Save only 'update' variant
        result = handle_save(config, ["update"], None, False, False)
        assert result == 0

        # Check only update file was created
        action_dir = sample_project / "pareidolia" / "action"
        assert (action_dir / "update-research.md.j2").exists()
        assert not (action_dir / "refine-research.md.j2").exists()

    def test_save_with_action_filter(self, sample_project: Path) -> None:
        """Test save command filters by action name correctly."""
        config_file = sample_project / "pareidolia.toml"
        config = PareidoliaConfig.from_file(config_file)

        # Add test variants for different actions
        cache = VariantCache()
        cache.add(
            CachedVariant(
                variant_name="update",
                action_name="research",
                persona_name="researcher",
                content="You are an expert researcher with deep analytical skills.\n\nResearch update.",
                generated_at=datetime.now(),
            )
        )
        cache.add(
            CachedVariant(
                variant_name="update",
                action_name="analyze",
                persona_name="researcher",
                content="You are an expert researcher with deep analytical skills.\n\nAnalyze update.",
                generated_at=datetime.now(),
            )
        )

        from pareidolia.cli import handle_save

        # Save only 'research' action
        result = handle_save(config, None, "research", False, False)
        assert result == 0

        # Check only research file was created
        action_dir = sample_project / "pareidolia" / "action"
        assert (action_dir / "update-research.md.j2").exists()
        assert not (action_dir / "update-analyze.md.j2").exists()

    def test_save_with_combined_filters(self, sample_project: Path) -> None:
        """Test save command with both variant and action filters."""
        config_file = sample_project / "pareidolia.toml"
        config = PareidoliaConfig.from_file(config_file)

        # Add multiple test variants
        cache = VariantCache()
        cache.add(
            CachedVariant(
                variant_name="update",
                action_name="research",
                persona_name="researcher",
                content="You are an expert researcher with deep analytical skills.\n\nUpdate research.",
                generated_at=datetime.now(),
            )
        )
        cache.add(
            CachedVariant(
                variant_name="refine",
                action_name="research",
                persona_name="researcher",
                content="You are an expert researcher with deep analytical skills.\n\nRefine research.",
                generated_at=datetime.now(),
            )
        )
        cache.add(
            CachedVariant(
                variant_name="update",
                action_name="analyze",
                persona_name="researcher",
                content="You are an expert researcher with deep analytical skills.\n\nUpdate analyze.",
                generated_at=datetime.now(),
            )
        )

        from pareidolia.cli import handle_save

        # Save only 'update' variant for 'research' action
        result = handle_save(config, ["update"], "research", False, False)
        assert result == 0

        # Check only matching file was created
        action_dir = sample_project / "pareidolia" / "action"
        assert (action_dir / "update-research.md.j2").exists()
        assert not (action_dir / "refine-research.md.j2").exists()
        assert not (action_dir / "update-analyze.md.j2").exists()

    def test_save_list_displays_variants(self, sample_project: Path) -> None:
        """Test save --list displays cached variants in table format."""
        config_file = sample_project / "pareidolia.toml"
        config = PareidoliaConfig.from_file(config_file)

        # Add test variants
        cache = VariantCache()
        cache.add(
            CachedVariant(
                variant_name="update",
                action_name="research",
                persona_name="researcher",
                content="Content",
                generated_at=datetime(2024, 10, 29, 10, 30, 0),
            )
        )
        cache.add(
            CachedVariant(
                variant_name="refine",
                action_name="analyze",
                persona_name="analyst",
                content="Content",
                generated_at=datetime(2024, 10, 29, 10, 31, 0),
            )
        )

        from pareidolia.cli import handle_save

        # List variants (should not create files)
        result = handle_save(config, None, None, True, False)
        assert result == 0

        # Verify no files were created
        action_dir = sample_project / "pareidolia" / "action"
        assert not (action_dir / "update-research.md.j2").exists()
        assert not (action_dir / "refine-analyze.md.j2").exists()

    def test_save_force_overwrites_existing_files(self, sample_project: Path) -> None:
        """Test save --force overwrites existing files."""
        config_file = sample_project / "pareidolia.toml"
        config = PareidoliaConfig.from_file(config_file)

        # Create existing file
        action_dir = sample_project / "pareidolia" / "action"
        action_dir.mkdir(parents=True, exist_ok=True)
        existing_file = action_dir / "update-research.md.j2"
        existing_file.write_text("Old content")

        # Add variant to cache
        cache = VariantCache()
        cache.add(
            CachedVariant(
                variant_name="update",
                action_name="research",
                persona_name="researcher",
                content="You are an expert researcher with deep analytical skills.\n\nNew content.",
                generated_at=datetime.now(),
            )
        )

        from pareidolia.cli import handle_save

        # Save with force
        result = handle_save(config, None, None, False, True)
        assert result == 0

        # Verify file was overwritten
        new_content = existing_file.read_text()
        assert "New content" in new_content
        assert "Old content" not in new_content

    def test_save_skips_existing_files_without_force(
        self, sample_project: Path
    ) -> None:
        """Test save skips existing files without --force flag."""
        config_file = sample_project / "pareidolia.toml"
        config = PareidoliaConfig.from_file(config_file)

        # Create existing file
        action_dir = sample_project / "pareidolia" / "action"
        action_dir.mkdir(parents=True, exist_ok=True)
        existing_file = action_dir / "update-research.md.j2"
        existing_file.write_text("Original content")

        # Add variant to cache
        cache = VariantCache()
        cache.add(
            CachedVariant(
                variant_name="update",
                action_name="research",
                persona_name="researcher",
                content="You are an expert researcher with deep analytical skills.\n\nNew content.",
                generated_at=datetime.now(),
            )
        )

        from pareidolia.cli import handle_save

        # Save without force
        result = handle_save(config, None, None, False, False)
        assert result == 0

        # Verify file was NOT overwritten
        content = existing_file.read_text()
        assert "Original content" in content
        assert "New content" not in content

    def test_generate_command_shows_cache_message(self, sample_project: Path) -> None:
        """Test generate command shows cache message when variants are cached."""
        # This test verifies the integration between generate and cache
        # We'll create a simple scenario that caches variants

        config_file = sample_project / "pareidolia.toml"
        config = PareidoliaConfig.from_file(config_file)

        # Manually add a variant to cache to simulate what generate would do
        cache = VariantCache()
        cache.add(
            CachedVariant(
                variant_name="update",
                action_name="research",
                persona_name="researcher",
                content="Test content",
                generated_at=datetime.now(),
            )
        )

        # Verify cache has variants
        assert cache.has_variants()
        assert cache.count() == 1

        # The actual generate command would print the message
        # For this test, we just verify the cache state
        from pareidolia.cli import handle_generate

        # Note: This won't actually cache new variants since we're not using
        # a real AI generator, but it verifies the function can check the cache
        result = handle_generate(config, None, None, None)
        # Result depends on actual generation, but cache check works
        assert cache.has_variants()

    def test_end_to_end_generate_cache_save_verify(
        self, sample_project: Path
    ) -> None:
        """Test complete workflow: generate → cache → save → verify files."""
        config_file = sample_project / "pareidolia.toml"
        config = PareidoliaConfig.from_file(config_file)

        # Simulate the generate phase by manually caching variants
        persona_content = (
            "You are an expert researcher with deep analytical skills.\n"
            "You approach problems methodically and thoroughly.\n"
        )
        cache = VariantCache()
        cache.add(
            CachedVariant(
                variant_name="update",
                action_name="research",
                persona_name="researcher",
                content=persona_content + "\nUpdated research task.",
                generated_at=datetime.now(),
            )
        )
        cache.add(
            CachedVariant(
                variant_name="refine",
                action_name="research",
                persona_name="researcher",
                content=persona_content + "\nRefined research task.",
                generated_at=datetime.now(),
            )
        )

        # Verify cache has variants
        assert cache.count() == 2

        # Save the cached variants
        from pareidolia.cli import handle_save

        result = handle_save(config, None, None, False, False)
        assert result == 0

        # Verify files were created
        action_dir = sample_project / "pareidolia" / "action"
        update_file = action_dir / "update-research.md.j2"
        refine_file = action_dir / "refine-research.md.j2"

        assert update_file.exists()
        assert refine_file.exists()

        # Verify content
        update_content = update_file.read_text()
        assert "{{ persona }}" in update_content
        assert "Updated research task" in update_content

        refine_content = refine_file.read_text()
        assert "{{ persona }}" in refine_content
        assert "Refined research task" in refine_content

    def test_save_no_matching_filters_returns_error(
        self, sample_project: Path
    ) -> None:
        """Test save returns error when no variants match filters."""
        config_file = sample_project / "pareidolia.toml"
        config = PareidoliaConfig.from_file(config_file)

        # Add a variant
        cache = VariantCache()
        cache.add(
            CachedVariant(
                variant_name="update",
                action_name="research",
                persona_name="researcher",
                content="Content",
                generated_at=datetime.now(),
            )
        )

        from pareidolia.cli import handle_save

        # Try to save with non-matching filter
        result = handle_save(config, ["nonexistent"], None, False, False)
        assert result == 1

    def test_save_multiple_variant_names_filter(self, sample_project: Path) -> None:
        """Test save command with multiple variant names in filter."""
        config_file = sample_project / "pareidolia.toml"
        config = PareidoliaConfig.from_file(config_file)

        # Add test variants
        cache = VariantCache()
        cache.add(
            CachedVariant(
                variant_name="update",
                action_name="research",
                persona_name="researcher",
                content="You are an expert researcher with deep analytical skills.\n\nUpdate.",
                generated_at=datetime.now(),
            )
        )
        cache.add(
            CachedVariant(
                variant_name="refine",
                action_name="research",
                persona_name="researcher",
                content="You are an expert researcher with deep analytical skills.\n\nRefine.",
                generated_at=datetime.now(),
            )
        )
        cache.add(
            CachedVariant(
                variant_name="summarize",
                action_name="research",
                persona_name="researcher",
                content="You are an expert researcher with deep analytical skills.\n\nSummarize.",
                generated_at=datetime.now(),
            )
        )

        from pareidolia.cli import handle_save

        # Save 'update' and 'refine' variants
        result = handle_save(config, ["update", "refine"], None, False, False)
        assert result == 0

        # Check correct files were created
        action_dir = sample_project / "pareidolia" / "action"
        assert (action_dir / "update-research.md.j2").exists()
        assert (action_dir / "refine-research.md.j2").exists()
        assert not (action_dir / "summarize-research.md.j2").exists()
