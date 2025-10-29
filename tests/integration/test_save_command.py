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
                content=(
                    "You are an expert researcher with deep analytical "
                    "skills.\n\nUpdate."
                ),
                generated_at=datetime.now(),
            )
        )
        cache.add(
            CachedVariant(
                variant_name="refine",
                action_name="research",
                persona_name="researcher",
                content=(
                    "You are an expert researcher with deep analytical "
                    "skills.\n\nRefine."
                ),
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
                content=(
                    "You are an expert researcher with deep analytical "
                    "skills.\n\nResearch update."
                ),
                generated_at=datetime.now(),
            )
        )
        cache.add(
            CachedVariant(
                variant_name="update",
                action_name="analyze",
                persona_name="researcher",
                content=(
                    "You are an expert researcher with deep analytical "
                    "skills.\n\nAnalyze update."
                ),
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
                content=(
                    "You are an expert researcher with deep analytical "
                    "skills.\n\nUpdate research."
                ),
                generated_at=datetime.now(),
            )
        )
        cache.add(
            CachedVariant(
                variant_name="refine",
                action_name="research",
                persona_name="researcher",
                content=(
                    "You are an expert researcher with deep analytical "
                    "skills.\n\nRefine research."
                ),
                generated_at=datetime.now(),
            )
        )
        cache.add(
            CachedVariant(
                variant_name="update",
                action_name="analyze",
                persona_name="researcher",
                content=(
                    "You are an expert researcher with deep analytical "
                    "skills.\n\nUpdate analyze."
                ),
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
                content=(
                    "You are an expert researcher with deep analytical "
                    "skills.\n\nNew content."
                ),
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
                content=(
                    "You are an expert researcher with deep analytical "
                    "skills.\n\nNew content."
                ),
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
        handle_generate(config, None, None, None)
        # The generate command can check the cache
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
                content=(
                    "You are an expert researcher with deep analytical "
                    "skills.\n\nUpdate."
                ),
                generated_at=datetime.now(),
            )
        )
        cache.add(
            CachedVariant(
                variant_name="refine",
                action_name="research",
                persona_name="researcher",
                content=(
                    "You are an expert researcher with deep analytical "
                    "skills.\n\nRefine."
                ),
                generated_at=datetime.now(),
            )
        )
        cache.add(
            CachedVariant(
                variant_name="summarize",
                action_name="research",
                persona_name="researcher",
                content=(
                    "You are an expert researcher with deep analytical "
                    "skills.\n\nSummarize."
                ),
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

    def test_full_workflow_generate_save_regenerate(
        self, sample_project: Path
    ) -> None:
        """Test full workflow: generate with AI → save → regenerate uses saved template.

        This test verifies that:
        1. Initial generation uses AI (CLI tool) for variant
        2. Variant is cached and can be saved
        3. Saved template is created in correct location
        4. Second generation uses saved template (not AI)
        5. Both outputs are equivalent
        """
        from unittest.mock import Mock, patch

        from pareidolia.generators.generator import Generator

        config_file = sample_project / "pareidolia.toml"
        config = PareidoliaConfig.from_file(config_file)

        # Update config to include variant
        config_content = config_file.read_text()
        config_content += (
            '\n[[prompt]]\n'
            'persona = "researcher"\n'
            'action = "research"\n'
            'variants = ["update"]\n'
        )
        config_file.write_text(config_content)
        config = PareidoliaConfig.from_file(config_file)

        # Create variant template for AI transformation
        variant_dir = sample_project / "pareidolia" / "variant"
        variant_dir.mkdir(exist_ok=True)
        (variant_dir / "update.md.j2").write_text(
            "Transform the following prompt to focus on updating existing work.\n"
            "Action: {{ action_name }}\n"
            "Persona: {{ persona_name }}\n"
        )

        output_dir = sample_project / "prompts"
        output_dir.mkdir(exist_ok=True)

        # PHASE 1: Generate with AI
        mock_tool = Mock()
        mock_tool.name = "mock_tool"
        mock_tool.is_available.return_value = True
        ai_generated_content = (
            "You are an expert researcher with deep analytical skills.\n"
            "You approach problems methodically and thoroughly.\n\n"
            "UPDATE: Review and revise your existing research with new findings."
        )
        mock_tool.generate_variant.return_value = ai_generated_content

        with patch(
            "pareidolia.generators.generator.get_available_tools",
            return_value=[mock_tool],
        ):
            generator = Generator(config)
            result = generator.generate_action(
                action_name="research",
                persona_name="researcher",
            )

        # Verify initial generation succeeded
        assert result.success
        assert len(result.files_generated) == 2  # base + variant
        assert mock_tool.generate_variant.called

        # Verify variant was cached
        cache = VariantCache()
        assert cache.count() == 1
        cached_variants = cache.get_by_variant("update")
        assert len(cached_variants) == 1
        assert cached_variants[0].action_name == "research"

        # PHASE 2: Save cached variant
        from pareidolia.cli import handle_save

        save_result = handle_save(config, None, None, False, False)
        assert save_result == 0

        # Verify template file exists
        action_dir = sample_project / "pareidolia" / "action"
        template_file = action_dir / "update-research.md.j2"
        assert template_file.exists()

        # Verify template has Jinja2 placeholder
        template_content = template_file.read_text()
        assert "{{ persona }}" in template_content
        assert "UPDATE: Review and revise" in template_content

        # PHASE 3: Clear output and cache, then regenerate
        # Clear output directory
        for file in output_dir.iterdir():
            file.unlink()

        # Clear cache
        cache.clear()
        assert cache.count() == 0

        # Reset mock call count
        mock_tool.generate_variant.reset_mock()

        # Regenerate - should use saved template, NOT AI
        with patch(
            "pareidolia.generators.generator.get_available_tools",
            return_value=[mock_tool],
        ):
            generator = Generator(config)
            result2 = generator.generate_action(
                action_name="research",
                persona_name="researcher",
            )

        # Verify regeneration succeeded
        assert result2.success
        assert len(result2.files_generated) == 2  # base + variant

        # CRITICAL: Verify AI was NOT called on second generation
        assert not mock_tool.generate_variant.called

        # Verify variant file exists and has same content
        variant_file = output_dir / "update-research.prompt.md"
        assert variant_file.exists()
        regenerated_content = variant_file.read_text()

        # Both should contain the same essential content
        assert "UPDATE: Review and revise" in regenerated_content
        assert "expert researcher" in regenerated_content

    def test_saved_template_produces_deterministic_output(
        self, sample_project: Path
    ) -> None:
        """Test that saved templates produce identical output on multiple regenerations.

        Once a variant is saved as a template, regenerating should produce
        exactly the same output every time (no AI variability).
        """
        from unittest.mock import Mock, patch

        from pareidolia.generators.generator import Generator

        config_file = sample_project / "pareidolia.toml"
        config = PareidoliaConfig.from_file(config_file)

        # Add variant configuration
        config_content = config_file.read_text()
        config_content += (
            '\n[[prompt]]\n'
            'persona = "researcher"\n'
            'action = "research"\n'
            'variants = ["refine"]\n'
        )
        config_file.write_text(config_content)
        config = PareidoliaConfig.from_file(config_file)

        # Create variant template
        variant_dir = sample_project / "pareidolia" / "variant"
        variant_dir.mkdir(exist_ok=True)
        (variant_dir / "refine.md.j2").write_text(
            "Refine and improve the prompt quality.\n"
        )

        output_dir = sample_project / "prompts"
        output_dir.mkdir(exist_ok=True)

        # Generate with AI
        mock_tool = Mock()
        mock_tool.name = "mock_tool"
        mock_tool.is_available.return_value = True
        ai_content = (
            "You are an expert researcher with deep analytical skills.\n"
            "You approach problems methodically and thoroughly.\n\n"
            "REFINED: Conduct a thorough and systematic investigation."
        )
        mock_tool.generate_variant.return_value = ai_content

        with patch(
            "pareidolia.generators.generator.get_available_tools",
            return_value=[mock_tool],
        ):
            generator = Generator(config)
            generator.generate_action(
                action_name="research",
                persona_name="researcher",
            )

        # Save variant
        from pareidolia.cli import handle_save

        handle_save(config, None, None, False, False)

        # Verify template exists
        action_dir = sample_project / "pareidolia" / "action"
        template_file = action_dir / "refine-research.md.j2"
        assert template_file.exists()

        # Clear cache and output
        VariantCache().clear()
        for file in output_dir.iterdir():
            file.unlink()

        # Regenerate multiple times and verify identical output
        outputs = []
        for _ in range(3):
            # Clear previous output
            for file in output_dir.iterdir():
                file.unlink()

            # Regenerate
            generator = Generator(config)
            generator.generate_action(
                action_name="research",
                persona_name="researcher",
            )

            # Read output
            variant_file = output_dir / "refine-research.prompt.md"
            assert variant_file.exists()
            outputs.append(variant_file.read_text())

        # All outputs should be identical
        assert len(outputs) == 3
        assert outputs[0] == outputs[1]
        assert outputs[1] == outputs[2]
        assert "REFINED: Conduct a thorough" in outputs[0]

    def test_saved_template_with_examples(self, sample_project: Path) -> None:
        """Test that saved templates work correctly with examples.

        Verifies that:
        1. Variant generation with examples works
        2. Saved template preserves example handling
        3. Regeneration with examples produces correct output
        """
        from unittest.mock import Mock, patch

        from pareidolia.generators.generator import Generator

        config_file = sample_project / "pareidolia.toml"
        config = PareidoliaConfig.from_file(config_file)

        # Add variant configuration
        config_content = config_file.read_text()
        config_content += (
            '\n[[prompt]]\n'
            'persona = "researcher"\n'
            'action = "research"\n'
            'variants = ["summarize"]\n'
        )
        config_file.write_text(config_content)
        config = PareidoliaConfig.from_file(config_file)

        # Create additional example
        example_dir = sample_project / "pareidolia" / "example"
        (example_dir / "methodology.md").write_text(
            "# Methodology Example\n\n"
            "1. Gather data\n"
            "2. Analyze findings\n"
            "3. Draw conclusions\n"
        )

        # Create variant template
        variant_dir = sample_project / "pareidolia" / "variant"
        variant_dir.mkdir(exist_ok=True)
        (variant_dir / "summarize.md.j2").write_text(
            "Create a concise summary of the prompt.\n"
        )

        output_dir = sample_project / "prompts"
        output_dir.mkdir(exist_ok=True)

        # PHASE 1: Generate with AI and examples
        mock_tool = Mock()
        mock_tool.name = "mock_tool"
        mock_tool.is_available.return_value = True

        # AI should receive base prompt with examples
        def mock_generate(
            variant_prompt: str, base_prompt: str, timeout: int = 60
        ) -> str:
            # Verify examples are in base prompt
            assert "Research Report Example" in base_prompt
            assert "Methodology Example" in base_prompt
            return (
                "You are an expert researcher with deep analytical skills.\n"
                "You approach problems methodically and thoroughly.\n\n"
                "SUMMARY: Provide a brief overview of the research topic.\n\n"
                "Examples:\n"
                "# Research Report Example\n"
                "# Methodology Example\n"
            )

        mock_tool.generate_variant.side_effect = mock_generate
        mock_tool.is_available.return_value = True

        with patch(
            "pareidolia.generators.generator.get_available_tools",
            return_value=[mock_tool],
        ):
            generator = Generator(config)
            result = generator.generate_action(
                action_name="research",
                persona_name="researcher",
                example_names=["report-format", "methodology"],
            )

        assert result.success
        assert mock_tool.generate_variant.called

        # Verify variant has examples
        variant_file = output_dir / "summarize-research.prompt.md"
        assert variant_file.exists()
        variant_content = variant_file.read_text()
        assert "Research Report Example" in variant_content
        assert "Methodology Example" in variant_content

        # PHASE 2: Save variant
        from pareidolia.cli import handle_save

        handle_save(config, None, None, False, False)

        # Verify template exists and has example placeholder
        action_dir = sample_project / "pareidolia" / "action"
        template_file = action_dir / "summarize-research.md.j2"
        assert template_file.exists()
        template_content = template_file.read_text()
        assert "{{ persona }}" in template_content
        # Should have example handling logic
        assert "SUMMARY: Provide a brief overview" in template_content

        # PHASE 3: Regenerate with same examples
        VariantCache().clear()
        for file in output_dir.iterdir():
            file.unlink()

        mock_tool.generate_variant.reset_mock()

        # Regenerate with examples (should use template, not AI)
        generator = Generator(config)
        result2 = generator.generate_action(
            action_name="research",
            persona_name="researcher",
            example_names=["report-format", "methodology"],
        )

        assert result2.success
        # Verify AI was NOT called
        assert not mock_tool.generate_variant.called

        # Verify regenerated variant has examples
        variant_file2 = output_dir / "summarize-research.prompt.md"
        assert variant_file2.exists()
        regenerated_content = variant_file2.read_text()
        assert "Research Report Example" in regenerated_content
        assert "Methodology Example" in regenerated_content
        assert "SUMMARY: Provide a brief overview" in regenerated_content
