"""Integration tests for base action variant generation (Phase 3)."""

from unittest.mock import Mock, patch

import pytest

from pareidolia.core.config import GenerateConfig, PareidoliaConfig, PromptConfig
from pareidolia.generators.generator import Generator
from pareidolia.generators.variant_cache import VariantCache


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear the variant cache before each test."""
    VariantCache().clear()


@pytest.fixture
def temp_project_dir(tmp_path):
    """Create a temporary project directory with minimal structure."""
    # Create persona
    persona_dir = tmp_path / "persona"
    persona_dir.mkdir()
    (persona_dir / "researcher.md").write_text(
        "You are an expert researcher with deep analytical skills."
    )

    # Create base action
    action_dir = tmp_path / "action"
    action_dir.mkdir()
    (action_dir / "research.md.j2").write_text(
        "Research the following topic:\n{{ persona }}\n\nProvide detailed findings."
    )

    # Create variant templates for AI fallback
    variant_dir = tmp_path / "variant"
    variant_dir.mkdir()
    (variant_dir / "update.md.j2").write_text(
        "Transform to update variant for {{ action_name }}"
    )
    (variant_dir / "refine.md.j2").write_text(
        "Transform to refine variant for {{ action_name }}"
    )

    return tmp_path


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary output directory."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


def test_variant_generated_from_action_template(temp_project_dir, temp_output_dir):
    """Test that variant is generated from action template when it exists."""
    # Create action template for variant (update-research.md.j2)
    action_dir = temp_project_dir / "action"
    variant_action_path = action_dir / "update-research.md.j2"
    variant_action_path.write_text(
        "{{ persona }}\n\n"
        "Update the research on this topic.\n\n"
        "This is a direct template."
    )

    # Create config with prompts
    generate_config = GenerateConfig(
        tool="copilot",
        library=None,
        output_dir=temp_output_dir,
    )

    prompt_config = PromptConfig(
        persona="researcher",
        action="research",
        variants=["update"],
        cli_tool=None,
    )

    config = PareidoliaConfig(
        root=temp_project_dir,
        generate=generate_config,
        metadata={},
        prompt=[prompt_config],
    )

    # Generate
    generator = Generator(config)
    result = generator.generate_action(
        action_name="research",
        persona_name="researcher",
    )

    # Verify generation succeeded
    assert result.success

    # Should have 2 files: base + variant
    assert len(result.files_generated) == 2

    # Verify variant was generated
    assert any("update-research" in str(p) for p in result.files_generated)

    # Verify content came from action template (not AI)
    variant_file = [p for p in result.files_generated if "update-research" in str(p)][
        0
    ]
    content = variant_file.read_text()
    assert "Update the research on this topic" in content
    assert "This is a direct template" in content
    # Should NOT contain AI generation markers
    assert "Generated variant based on:" not in content


def test_variant_falls_back_to_ai_when_no_action_template(
    temp_project_dir, temp_output_dir
):
    """Test that variant falls back to AI when action template doesn't exist."""
    # No update-research.md.j2 created
    # Only variant template exists (already created in fixture)

    generate_config = GenerateConfig(
        tool="copilot",
        library=None,
        output_dir=temp_output_dir,
    )

    prompt_config = PromptConfig(
        persona="researcher",
        action="research",
        variants=["update"],
        cli_tool=None,
    )

    config = PareidoliaConfig(
        root=temp_project_dir,
        generate=generate_config,
        metadata={},
        prompt=[prompt_config],
    )

    # Mock CLI tool
    mock_tool = Mock()
    mock_tool.name = "mock_tool"
    mock_tool.is_available.return_value = True
    mock_tool.generate_variant.return_value = "AI generated variant content"

    with patch(
        "pareidolia.generators.generator.get_available_tools",
        return_value=[mock_tool],
    ):
        generator = Generator(config)
        result = generator.generate_action(
            action_name="research",
            persona_name="researcher",
        )

    # Verify generation succeeded
    assert result.success

    # Should have 2 files: base + variant
    assert len(result.files_generated) == 2

    # Verify AI was called
    assert mock_tool.generate_variant.called

    # Verify variant file exists
    variant_file = temp_output_dir / "update-research.prompt.md"
    assert variant_file.exists()

    # Verify content came from AI
    content = variant_file.read_text()
    assert content == "AI generated variant content"


def test_mixed_direct_and_ai_variants(temp_project_dir, temp_output_dir):
    """Test mixed scenario with some direct templates and some AI fallback."""
    # Create action template for update (direct)
    action_dir = temp_project_dir / "action"
    (action_dir / "update-research.md.j2").write_text(
        "{{ persona }}\n\nUpdate variant from direct template."
    )

    # Don't create action/refine-research.md.j2 (will use AI)
    # variant/refine.md.j2 already exists from fixture

    generate_config = GenerateConfig(
        tool="copilot",
        library=None,
        output_dir=temp_output_dir,
    )

    prompt_config = PromptConfig(
        persona="researcher",
        action="research",
        variants=["update", "refine"],
        cli_tool=None,
    )

    config = PareidoliaConfig(
        root=temp_project_dir,
        generate=generate_config,
        metadata={},
        prompt=[prompt_config],
    )

    # Mock CLI tool for AI fallback
    mock_tool = Mock()
    mock_tool.name = "mock_tool"
    mock_tool.is_available.return_value = True
    mock_tool.generate_variant.return_value = "AI refined variant content"

    with patch(
        "pareidolia.generators.generator.get_available_tools",
        return_value=[mock_tool],
    ):
        generator = Generator(config)
        result = generator.generate_action(
            action_name="research",
            persona_name="researcher",
        )

    # Verify generation succeeded
    assert result.success

    # Should have 3 files: base + 2 variants
    assert len(result.files_generated) == 3

    # Verify update was generated from template
    update_file = temp_output_dir / "update-research.prompt.md"
    assert update_file.exists()
    update_content = update_file.read_text()
    assert "Update variant from direct template" in update_content

    # Verify refine was generated via AI
    refine_file = temp_output_dir / "refine-research.prompt.md"
    assert refine_file.exists()
    refine_content = refine_file.read_text()
    assert refine_content == "AI refined variant content"

    # Verify AI was called only once (for refine, not update)
    assert mock_tool.generate_variant.call_count == 1


def test_all_variants_from_action_templates(temp_project_dir, temp_output_dir):
    """Test that all variants can be generated from action templates (no AI needed)."""
    # Create action templates for all variants
    action_dir = temp_project_dir / "action"
    (action_dir / "update-research.md.j2").write_text(
        "{{ persona }}\n\nUpdate from template."
    )
    (action_dir / "refine-research.md.j2").write_text(
        "{{ persona }}\n\nRefine from template."
    )

    generate_config = GenerateConfig(
        tool="copilot",
        library=None,
        output_dir=temp_output_dir,
    )

    prompt_config = PromptConfig(
        persona="researcher",
        action="research",
        variants=["update", "refine"],
        cli_tool=None,  # No CLI tool needed
    )

    config = PareidoliaConfig(
        root=temp_project_dir,
        generate=generate_config,
        metadata={},
        prompt=[prompt_config],
    )

    # Generate without mocking any CLI tools
    generator = Generator(config)
    result = generator.generate_action(
        action_name="research",
        persona_name="researcher",
    )

    # Verify generation succeeded
    assert result.success

    # Should have 3 files: base + 2 variants
    assert len(result.files_generated) == 3

    # Verify both variants exist and contain template content
    update_file = temp_output_dir / "update-research.prompt.md"
    assert update_file.exists()
    assert "Update from template" in update_file.read_text()

    refine_file = temp_output_dir / "refine-research.prompt.md"
    assert refine_file.exists()
    assert "Refine from template" in refine_file.read_text()


def test_direct_variant_with_library_prefix(temp_project_dir, temp_output_dir):
    """Test that direct variant action templates work with library prefix."""
    # Create action template for variant
    action_dir = temp_project_dir / "action"
    (action_dir / "update-research.md.j2").write_text(
        "{{ persona }}\n\nUpdate variant with library."
    )

    generate_config = GenerateConfig(
        tool="copilot",
        library="mylib",
        output_dir=temp_output_dir,
    )

    prompt_config = PromptConfig(
        persona="researcher",
        action="research",
        variants=["update"],
        cli_tool=None,
    )

    config = PareidoliaConfig(
        root=temp_project_dir,
        generate=generate_config,
        metadata={},
        prompt=[prompt_config],
    )

    generator = Generator(config)
    result = generator.generate_action(
        action_name="research",
        persona_name="researcher",
    )

    # Verify generation succeeded
    assert result.success

    # Base file with library prefix
    base_file = temp_output_dir / "mylib.research.prompt.md"
    assert base_file.exists()

    # Variant file with library prefix applied to full action name
    variant_file = temp_output_dir / "mylib.update-research.prompt.md"
    assert variant_file.exists()

    # Verify content is from template
    content = variant_file.read_text()
    assert "Update variant with library" in content


def test_generate_all_with_mixed_variants(temp_project_dir, temp_output_dir):
    """Test generate_all with mixed direct and AI variant generation."""
    # Create action templates
    action_dir = temp_project_dir / "action"
    (action_dir / "analyze.md.j2").write_text("{{ persona }}\n\nAnalyze this.")
    (action_dir / "update-research.md.j2").write_text(
        "{{ persona }}\n\nUpdate variant."
    )

    generate_config = GenerateConfig(
        tool="copilot",
        library=None,
        output_dir=temp_output_dir,
    )

    prompt_config = PromptConfig(
        persona="researcher",
        action="research",
        variants=["update", "refine"],
        cli_tool=None,
    )

    config = PareidoliaConfig(
        root=temp_project_dir,
        generate=generate_config,
        metadata={},
        prompt=[prompt_config],
    )

    # Mock CLI tool for refine (AI fallback)
    mock_tool = Mock()
    mock_tool.name = "mock_tool"
    mock_tool.is_available.return_value = True
    mock_tool.generate_variant.return_value = "AI refine content"

    with patch(
        "pareidolia.generators.generator.get_available_tools",
        return_value=[mock_tool],
    ):
        generator = Generator(config)
        result = generator.generate_all(persona_name="researcher")

    # Should succeed
    assert result.success

    # Should have:
    # - analyze.prompt.md (base only)
    # - research.prompt.md (base)
    # - update-research.prompt.md (variant from template)
    # - refine-research.prompt.md (variant from AI)
    assert len(result.files_generated) == 4

    # Verify files exist
    assert (temp_output_dir / "analyze.prompt.md").exists()
    assert (temp_output_dir / "research.prompt.md").exists()
    assert (temp_output_dir / "update-research.prompt.md").exists()
    assert (temp_output_dir / "refine-research.prompt.md").exists()

    # No variants for analyze
    assert not (temp_output_dir / "update-analyze.prompt.md").exists()

    # Verify update came from template
    update_content = (temp_output_dir / "update-research.prompt.md").read_text()
    assert "Update variant" in update_content

    # Verify refine came from AI
    refine_content = (temp_output_dir / "refine-research.prompt.md").read_text()
    assert refine_content == "AI refine content"


def test_direct_variant_with_examples(temp_project_dir, temp_output_dir):
    """Test that direct variant templates receive example names."""
    # Create action template for variant with examples
    action_dir = temp_project_dir / "action"
    (action_dir / "update-research.md.j2").write_text(
        "{{ persona }}\\n\\nUpdate variant.\\n\\n"
        "{% if examples %}Examples:\\n"
        "{% for example in examples %}{{ example }}\\n{% endfor %}"
        "{% endif %}"
    )

    # Create example files
    example_dir = temp_project_dir / "example"
    example_dir.mkdir()
    (example_dir / "sample1.md").write_text("Example 1 content")
    (example_dir / "sample2.md").write_text("Example 2 content")

    generate_config = GenerateConfig(
        tool="copilot",
        library=None,
        output_dir=temp_output_dir,
    )

    prompt_config = PromptConfig(
        persona="researcher",
        action="research",
        variants=["update"],
        cli_tool=None,
    )

    config = PareidoliaConfig(
        root=temp_project_dir,
        generate=generate_config,
        metadata={},
        prompt=[prompt_config],
    )

    generator = Generator(config)
    result = generator.generate_action(
        action_name="research",
        persona_name="researcher",
        example_names=["sample1", "sample2"],
    )

    # Verify generation succeeded
    assert result.success

    # Verify variant includes examples
    variant_file = temp_output_dir / "update-research.prompt.md"
    assert variant_file.exists()
    content = variant_file.read_text()
    assert "Examples:" in content
    assert "Example 1 content" in content
    assert "Example 2 content" in content


def test_ai_fallback_continues_on_cli_tool_error(temp_project_dir, temp_output_dir):
    """Test that generation continues when AI fallback fails."""
    # Create one direct template and one that will use AI (and fail)
    action_dir = temp_project_dir / "action"
    (action_dir / "update-research.md.j2").write_text(
        "{{ persona }}\n\nUpdate variant."
    )

    generate_config = GenerateConfig(
        tool="copilot",
        library=None,
        output_dir=temp_output_dir,
    )

    prompt_config = PromptConfig(
        persona="researcher",
        action="research",
        variants=["update", "refine"],  # refine will fail
        cli_tool=None,
    )

    config = PareidoliaConfig(
        root=temp_project_dir,
        generate=generate_config,
        metadata={},
        prompt=[prompt_config],
    )

    # Mock CLI tool that raises an error
    mock_tool = Mock()
    mock_tool.name = "mock_tool"
    mock_tool.is_available.return_value = True
    mock_tool.generate_variant.side_effect = Exception("CLI tool error")

    with patch(
        "pareidolia.generators.generator.get_available_tools",
        return_value=[mock_tool],
    ):
        generator = Generator(config)
        result = generator.generate_action(
            action_name="research",
            persona_name="researcher",
        )

    # Should still succeed (base + direct variant generated)
    assert result.success

    # Should have 2 files: base + update (refine failed)
    assert len(result.files_generated) == 2

    # Update exists (from template)
    assert (temp_output_dir / "update-research.prompt.md").exists()

    # Refine doesn't exist (AI failed)
    assert not (temp_output_dir / "refine-research.prompt.md").exists()


def test_logging_indicates_generation_strategy(
    temp_project_dir, temp_output_dir, caplog
):
    """Test that logging indicates which generation strategy was used."""
    import logging

    caplog.set_level(logging.INFO)

    # Create one direct template
    action_dir = temp_project_dir / "action"
    (action_dir / "update-research.md.j2").write_text(
        "{{ persona }}\n\nUpdate variant."
    )

    generate_config = GenerateConfig(
        tool="copilot",
        library=None,
        output_dir=temp_output_dir,
    )

    prompt_config = PromptConfig(
        persona="researcher",
        action="research",
        variants=["update", "refine"],
        cli_tool=None,
    )

    config = PareidoliaConfig(
        root=temp_project_dir,
        generate=generate_config,
        metadata={},
        prompt=[prompt_config],
    )

    # Mock CLI tool for AI fallback
    mock_tool = Mock()
    mock_tool.name = "mock_tool"
    mock_tool.is_available.return_value = True
    mock_tool.generate_variant.return_value = "AI content"

    with patch(
        "pareidolia.generators.generator.get_available_tools",
        return_value=[mock_tool],
    ):
        generator = Generator(config)
        generator.generate_action(
            action_name="research",
            persona_name="researcher",
        )

    # Check that logs indicate the generation strategy
    log_messages = [rec.message for rec in caplog.records]

    # Should have log for direct template generation
    assert any(
        "action template" in msg for msg in log_messages
    ), "Missing log for direct template generation"

    # Should have log for AI transformation
    assert any(
        "AI transformation" in msg for msg in log_messages
    ), "Missing log for AI transformation"


def test_ai_variant_is_cached(temp_project_dir, temp_output_dir):
    """Test that AI-generated variants are cached."""
    # No action template for variant (will use AI)
    generate_config = GenerateConfig(
        tool="copilot",
        library=None,
        output_dir=temp_output_dir,
    )

    prompt_config = PromptConfig(
        persona="researcher",
        action="research",
        variants=["update"],
        cli_tool=None,
        metadata={"project": "test-project", "version": "1.0"},
    )

    config = PareidoliaConfig(
        root=temp_project_dir,
        generate=generate_config,
        metadata={},
        prompt=[prompt_config],
    )

    # Mock CLI tool
    mock_tool = Mock()
    mock_tool.name = "mock_tool"
    mock_tool.is_available.return_value = True
    mock_tool.generate_variant.return_value = "AI generated variant content"

    cache = VariantCache()

    with patch(
        "pareidolia.generators.generator.get_available_tools",
        return_value=[mock_tool],
    ):
        generator = Generator(config)
        result = generator.generate_action(
            action_name="research",
            persona_name="researcher",
        )

    # Verify generation succeeded
    assert result.success

    # Verify variant was cached
    assert cache.count() == 1

    cached_variants = cache.get_all()
    assert len(cached_variants) == 1

    cached = cached_variants[0]
    assert cached.variant_name == "update"
    assert cached.action_name == "research"
    assert cached.persona_name == "researcher"
    assert cached.content == "AI generated variant content"
    assert cached.metadata == {"project": "test-project", "version": "1.0"}
    assert cached.generated_at is not None


def test_template_variant_not_cached(temp_project_dir, temp_output_dir):
    """Test that template-based variants are NOT cached."""
    # Create action template for variant (direct generation)
    action_dir = temp_project_dir / "action"
    (action_dir / "update-research.md.j2").write_text(
        "{{ persona }}\n\nUpdate variant from template."
    )

    generate_config = GenerateConfig(
        tool="copilot",
        library=None,
        output_dir=temp_output_dir,
    )

    prompt_config = PromptConfig(
        persona="researcher",
        action="research",
        variants=["update"],
        cli_tool=None,
    )

    config = PareidoliaConfig(
        root=temp_project_dir,
        generate=generate_config,
        metadata={},
        prompt=[prompt_config],
    )

    cache = VariantCache()

    generator = Generator(config)
    result = generator.generate_action(
        action_name="research",
        persona_name="researcher",
    )

    # Verify generation succeeded
    assert result.success

    # Verify variant was NOT cached (template-based)
    assert cache.count() == 0
    assert not cache.has_variants()


def test_multiple_variants_cached_in_single_generation(
    temp_project_dir, temp_output_dir
):
    """Test that multiple AI variants are all cached in a single generation."""
    # Create variant templates for AI fallback
    variant_dir = temp_project_dir / "variant"
    (variant_dir / "expand.md.j2").write_text(
        "Transform to expand variant for {{ action_name }}"
    )

    # No action templates for variants (all will use AI)
    generate_config = GenerateConfig(
        tool="copilot",
        library=None,
        output_dir=temp_output_dir,
    )

    prompt_config = PromptConfig(
        persona="researcher",
        action="research",
        variants=["update", "refine", "expand"],
        cli_tool=None,
        metadata={"category": "analysis"},
    )

    config = PareidoliaConfig(
        root=temp_project_dir,
        generate=generate_config,
        metadata={},
        prompt=[prompt_config],
    )

    # Mock CLI tool
    mock_tool = Mock()
    mock_tool.name = "mock_tool"
    mock_tool.is_available.return_value = True

    # Return different content for each variant
    mock_tool.generate_variant.side_effect = [
        "Update variant content",
        "Refine variant content",
        "Expand variant content",
    ]

    cache = VariantCache()

    with patch(
        "pareidolia.generators.generator.get_available_tools",
        return_value=[mock_tool],
    ):
        generator = Generator(config)
        result = generator.generate_action(
            action_name="research",
            persona_name="researcher",
        )

    # Verify generation succeeded
    assert result.success

    # Verify all 3 variants were cached
    assert cache.count() == 3

    # Verify each variant
    update_variants = cache.get_by_variant("update")
    assert len(update_variants) == 1
    assert update_variants[0].content == "Update variant content"
    assert update_variants[0].metadata == {"category": "analysis"}

    refine_variants = cache.get_by_variant("refine")
    assert len(refine_variants) == 1
    assert refine_variants[0].content == "Refine variant content"

    expand_variants = cache.get_by_variant("expand")
    assert len(expand_variants) == 1
    assert expand_variants[0].content == "Expand variant content"

    # Verify all are for the same action
    research_variants = cache.get_by_action("research")
    assert len(research_variants) == 3

