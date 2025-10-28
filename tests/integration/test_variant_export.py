"""Integration tests for variant export functionality."""

from unittest.mock import Mock, patch

import pytest

from pareidolia.core.config import GenerateConfig, PareidoliaConfig, PromptConfig
from pareidolia.generators.generator import Generator


@pytest.fixture
def temp_project_dir(tmp_path):
    """Create a temporary project directory with minimal structure."""
    # Create persona
    persona_dir = tmp_path / "persona"
    persona_dir.mkdir()
    (persona_dir / "researcher.md").write_text(
        "You are an expert researcher with deep analytical skills."
    )

    # Create action
    action_dir = tmp_path / "action"
    action_dir.mkdir()
    (action_dir / "research.md.j2").write_text(
        "Research the following topic:\n{{ persona }}\n\nProvide detailed findings."
    )

    # Create variant templates
    variant_dir = tmp_path / "variant"
    variant_dir.mkdir()
    (variant_dir / "update.md.j2").write_text(
        "Transform to update variant for {{ action_name }}"
    )
    (variant_dir / "refine.md.j2").write_text(
        "Transform to refine variant for {{ action_name }}"
    )
    (variant_dir / "summarize.md.j2").write_text(
        "Transform to summarize variant for {{ action_name }}"
    )

    return tmp_path


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary output directory."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def config_with_variants(temp_project_dir, temp_output_dir):
    """Create configuration with variants enabled."""
    generate_config = GenerateConfig(
        tool="copilot",
        library=None,
        output_dir=temp_output_dir,
    )

    prompt_config = PromptConfig(
        persona="researcher",
        action="research",
        variants=["update", "refine", "summarize"],
        cli_tool=None,
    )

    return PareidoliaConfig(
        root=temp_project_dir,
        generate=generate_config,
        metadata={},
        prompt=[prompt_config],
    )


@pytest.fixture
def config_without_variants(temp_project_dir, temp_output_dir):
    """Create configuration without variants."""
    generate_config = GenerateConfig(
        tool="copilot",
        library=None,
        output_dir=temp_output_dir,
    )

    return PareidoliaConfig(
        root=temp_project_dir,
        generate=generate_config,
        metadata={},
        prompt=[],
    )


@pytest.fixture
def mock_cli_tool():
    """Create a mock CLI tool."""
    tool = Mock()
    tool.name = "mock_tool"
    tool.command = "mock"
    tool.is_available.return_value = True
    tool.generate_variant.side_effect = lambda variant_prompt, base_prompt, timeout: (
        f"Generated variant based on:\n{variant_prompt}\n\nFrom base:\n{base_prompt}"
    )
    return tool


def test_export_with_variants_generates_all_files(
    config_with_variants, mock_cli_tool, temp_output_dir
):
    """Test that export with variants generates base prompt and all variant files."""
    with patch(
        "pareidolia.generators.generator.get_available_tools",
        return_value=[mock_cli_tool],
    ):
        generator = Generator(config_with_variants)
        result = generator.generate_action(
            action_name="research",
            persona_name="researcher",
        )

    # Should succeed
    assert result.success

    # Should generate 4 files: 1 base + 3 variants
    assert len(result.files_generated) == 4

    # Check base file exists (copilot naming: research.prompt.md)
    base_file = temp_output_dir / "research.prompt.md"
    assert base_file in result.files_generated
    assert base_file.exists()

    # Check variant files exist with correct naming (verb-noun pattern)
    variant_names = ["update", "refine", "summarize"]
    for variant_name in variant_names:
        # Variants use base filename stem: update-research.md
        variant_file = temp_output_dir / f"{variant_name}-research.prompt.md"
        assert variant_file in result.files_generated
        assert variant_file.exists()


def test_export_without_variants_skips_generation(
    config_without_variants, temp_output_dir
):
    """Test that export without variants only generates base prompt."""
    generator = Generator(config_without_variants)
    result = generator.generate_action(
        action_name="research",
        persona_name="researcher",
    )

    # Should succeed
    assert result.success

    # Should generate only 1 file (base prompt)
    assert len(result.files_generated) == 1

    # Check base file exists
    base_file = temp_output_dir / "research.prompt.md"
    assert base_file in result.files_generated
    assert base_file.exists()

    # Check no variant files exist
    variant_names = ["update", "refine", "summarize"]
    for variant_name in variant_names:
        variant_file = temp_output_dir / f"{variant_name}-research.prompt.md"
        assert not variant_file.exists()


def test_export_variants_only_for_matching_action(
    config_with_variants, mock_cli_tool, temp_output_dir, temp_project_dir
):
    """Test that variants are only generated when action matches config."""
    # Create another action that doesn't match
    action_dir = temp_project_dir / "action"
    (action_dir / "analyze.md.j2").write_text(
        "Analyze the following:\n{{ persona }}\n\nProvide insights."
    )

    with patch(
        "pareidolia.generators.generator.get_available_tools",
        return_value=[mock_cli_tool],
    ):
        generator = Generator(config_with_variants)

        # Export the matching action
        result_match = generator.generate_action(
            action_name="research",
            persona_name="researcher",
        )

        # Export the non-matching action
        result_no_match = generator.generate_action(
            action_name="analyze",
            persona_name="researcher",
        )

    # Matching action should generate variants
    assert result_match.success
    assert len(result_match.files_generated) == 4  # 1 base + 3 variants

    # Non-matching action should not generate variants
    assert result_no_match.success
    assert len(result_no_match.files_generated) == 1  # Only base

    # Verify files
    assert (temp_output_dir / "update-research.prompt.md").exists()
    assert not (temp_output_dir / "update-analyze.prompt.md").exists()


def test_variant_naming_follows_verb_noun_pattern(
    config_with_variants, mock_cli_tool, temp_output_dir
):
    """Test that variant files follow the verb-noun naming pattern."""
    with patch(
        "pareidolia.generators.generator.get_available_tools",
        return_value=[mock_cli_tool],
    ):
        generator = Generator(config_with_variants)
        result = generator.generate_action(
            action_name="research",
            persona_name="researcher",
        )

    assert result.success

    # Check naming pattern: {variant_name}-{base_filename}.md
    expected_names = [
        "update-research.prompt.md",
        "refine-research.prompt.md",
        "summarize-research.prompt.md",
    ]

    for expected_name in expected_names:
        variant_file = temp_output_dir / expected_name
        assert variant_file.exists(), f"Expected {expected_name} to exist"


def test_export_continues_on_variant_error(
    config_with_variants, mock_cli_tool, temp_output_dir
):
    """Test that export continues even if variant generation fails."""
    # Make the CLI tool raise an error for one variant
    def generate_variant_with_error(variant_prompt, base_prompt, timeout):
        if "refine" in variant_prompt:
            raise Exception("Simulated CLI tool failure")
        return f"Generated variant based on:\n{variant_prompt}"

    mock_cli_tool.generate_variant.side_effect = generate_variant_with_error

    with patch(
        "pareidolia.generators.generator.get_available_tools",
        return_value=[mock_cli_tool],
    ):
        generator = Generator(config_with_variants)
        result = generator.generate_action(
            action_name="research",
            persona_name="researcher",
        )

    # Export should still succeed (base prompt generated)
    assert result.success

    # Should have base + 2 variants (update and summarize, but not refine)
    assert len(result.files_generated) == 3

    # Base file exists
    assert (temp_output_dir / "research.prompt.md").exists()

    # Successful variants exist
    assert (temp_output_dir / "update-research.prompt.md").exists()
    assert (temp_output_dir / "summarize-research.prompt.md").exists()

    # Failed variant doesn't exist
    assert not (temp_output_dir / "refine-research.prompt.md").exists()


def test_export_all_generates_variants_for_matching_actions(
    config_with_variants, mock_cli_tool, temp_output_dir, temp_project_dir
):
    """Test that export_all generates variants only for matching actions."""
    # Create additional action
    action_dir = temp_project_dir / "action"
    (action_dir / "analyze.md.j2").write_text(
        "Analyze the following:\n{{ persona }}"
    )

    with patch(
        "pareidolia.generators.generator.get_available_tools",
        return_value=[mock_cli_tool],
    ):
        generator = Generator(config_with_variants)
        result = generator.generate_all(persona_name="researcher")

    # Should succeed
    assert result.success

    # Should have:
    # - analyze.prompt.md (base only)
    # - research.prompt.md (base)
    # - update-research.prompt.md (variant)
    # - refine-research.prompt.md (variant)
    # - summarize-research.prompt.md (variant)
    assert len(result.files_generated) == 5

    # Verify files
    assert (temp_output_dir / "analyze.prompt.md").exists()
    assert (temp_output_dir / "research.prompt.md").exists()
    assert (temp_output_dir / "update-research.prompt.md").exists()
    assert (temp_output_dir / "refine-research.prompt.md").exists()
    assert (temp_output_dir / "summarize-research.prompt.md").exists()

    # No variants for analyze
    assert not (temp_output_dir / "update-analyze.prompt.md").exists()


def test_variant_content_uses_base_prompt(
    config_with_variants, mock_cli_tool, temp_output_dir
):
    """Test that variant generation receives the base prompt content."""
    with patch(
        "pareidolia.generators.generator.get_available_tools",
        return_value=[mock_cli_tool],
    ):
        generator = Generator(config_with_variants)
        result = generator.generate_action(
            action_name="research",
            persona_name="researcher",
        )

    assert result.success

    # Read a variant file
    variant_file = temp_output_dir / "update-research.prompt.md"
    variant_content = variant_file.read_text()

    # Should contain both the variant prompt and base prompt
    assert "Generated variant based on:" in variant_content
    assert "From base:" in variant_content

    # Read base file
    base_file = temp_output_dir / "research.prompt.md"
    base_content = base_file.read_text()

    # Variant should reference the base content
    assert base_content in variant_content


def test_missing_variant_template_does_not_fail_export(
    config_with_variants, mock_cli_tool, temp_output_dir, temp_project_dir
):
    """Test that missing variant template doesn't fail the entire export."""
    # Remove one variant template
    variant_dir = temp_project_dir / "variant"
    (variant_dir / "refine.md.j2").unlink()

    with patch(
        "pareidolia.generators.generator.get_available_tools",
        return_value=[mock_cli_tool],
    ):
        generator = Generator(config_with_variants)
        result = generator.generate_action(
            action_name="research",
            persona_name="researcher",
        )

    # Should still succeed
    assert result.success

    # Should have base + 2 variants (update and summarize, not refine)
    assert len(result.files_generated) == 3

    # Check which files exist
    assert (temp_output_dir / "research.prompt.md").exists()
    assert (temp_output_dir / "update-research.prompt.md").exists()
    assert (temp_output_dir / "summarize-research.prompt.md").exists()
    assert not (temp_output_dir / "refine-research.prompt.md").exists()


def test_variant_generation_with_library_prefix(temp_project_dir, temp_output_dir):
    """Test that variant files use the correct naming when library prefix is present."""
    # Create config with library
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

    mock_tool = Mock()
    mock_tool.name = "mock_tool"
    mock_tool.is_available.return_value = True
    mock_tool.generate_variant.return_value = "Variant content"

    with patch(
        "pareidolia.generators.generator.get_available_tools",
        return_value=[mock_tool],
    ):
        generator = Generator(config)
        result = generator.generate_action(
            action_name="research",
            persona_name="researcher",
        )

    assert result.success

    # With library prefix, base file is mylib.research.prompt.md (copilot naming)
    base_file = temp_output_dir / "mylib.research.prompt.md"
    assert base_file.exists()

    # Variant should be mylib.update-research.prompt.md
    # (library prefix applied to full action name)
    variant_file = temp_output_dir / "mylib.update-research.prompt.md"
    assert variant_file.exists()


def test_variant_generation_with_metadata(
    temp_project_dir, temp_output_dir, mock_cli_tool
):
    """Test that variant generation has access to metadata context."""
    # Create variant template that uses metadata
    variant_dir = temp_project_dir / "variant"
    (variant_dir / "custom.md.j2").write_text(
        """Transform to {{ variant_name }} variant for {{ action_name }}
Tool: {{ tool }}
Library: {{ library }}
{% if metadata.description %}Description: {{ metadata.description }}{% endif %}
{% if metadata.model %}Model: {{ metadata.model }}{% endif %}"""
    )

    # Create config with metadata
    generate_config = GenerateConfig(
        tool="copilot",
        library="testlib",
        output_dir=temp_output_dir,
    )

    prompt_config = PromptConfig(
        persona="researcher",
        action="research",
        variants=["custom"],
        cli_tool=None,
        metadata={
            "description": "Custom research tool",
            "model": "claude-3.5-sonnet",
        },
    )

    config = PareidoliaConfig(
        root=temp_project_dir,
        generate=generate_config,
        metadata={},
        prompt=[prompt_config],
    )

    with patch(
        "pareidolia.generators.generator.get_available_tools",
        return_value=[mock_cli_tool],
    ):
        generator = Generator(config)
        result = generator.generate_action(
            action_name="research",
            persona_name="researcher",
        )

    assert result.success

    # Verify the mock was called with the rendered template that includes metadata
    mock_cli_tool.generate_variant.assert_called_once()
    call_args = mock_cli_tool.generate_variant.call_args
    variant_prompt = call_args.kwargs["variant_prompt"]

    # The rendered variant template should include metadata
    assert "Tool: copilot" in variant_prompt
    assert "Library: testlib" in variant_prompt
    assert "Description: Custom research tool" in variant_prompt
    assert "Model: claude-3.5-sonnet" in variant_prompt

