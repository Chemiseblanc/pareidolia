"""Unit tests for template loader."""

from pathlib import Path

import pytest
from conftest import create_template_loader

from pareidolia.core.exceptions import VariantTemplateNotFoundError
from pareidolia.templates.loader import TemplateLoader


class TestTemplateLoaderVariants:
    """Tests for variant template loading."""

    @pytest.fixture
    def loader(self, tmp_path: Path) -> TemplateLoader:
        """Create a TemplateLoader with test fixtures."""
        # Copy fixtures to tmp_path/variant directory structure
        fixtures_src = Path(__file__).parent.parent / "fixtures" / "variants"
        variant_dir = tmp_path / "variant"
        variant_dir.mkdir()

        # Copy all fixture files
        import shutil
        for file in fixtures_src.glob("*"):
            if file.is_file():
                shutil.copy(file, variant_dir)

        return create_template_loader(tmp_path)

    def test_load_variant_template_with_j2_extension(
        self, loader: TemplateLoader
    ) -> None:
        """Test loading variant template with .md.j2 extension."""
        content = loader.load_variant_template("update")
        assert "update" in content.lower()
        assert "{{ persona_name }}" in content
        assert "{{ action_name }}" in content
        assert "{{ variant_name }}" in content

    def test_load_variant_template_with_md_extension(
        self, loader: TemplateLoader
    ) -> None:
        """Test loading variant template with .md extension."""
        content = loader.load_variant_template("refine")
        assert "refine" in content.lower()
        assert "improving" in content.lower()

    def test_load_variant_template_with_jinja2_extension(
        self, loader: TemplateLoader
    ) -> None:
        """Test loading variant template with .md.jinja2 extension."""
        content = loader.load_variant_template("summarize")
        assert "summarize" in content.lower()
        assert "condensing" in content.lower()

    def test_load_variant_template_not_found(
        self, loader: TemplateLoader
    ) -> None:
        """Test that missing variant template raises error."""
        with pytest.raises(
            VariantTemplateNotFoundError,
            match="Variant template not found: nonexistent",
        ):
            loader.load_variant_template("nonexistent")

    def test_list_variants(self, loader: TemplateLoader) -> None:
        """Test listing all variant templates."""
        variants = loader.list_variants()
        assert "update" in variants
        assert "refine" in variants
        assert "summarize" in variants
        assert len(variants) == 3

    def test_list_variants_sorted(self, loader: TemplateLoader) -> None:
        """Test that variant list is sorted."""
        variants = loader.list_variants()
        assert variants == sorted(variants)

    def test_list_variants_empty_directory(self, tmp_path: Path) -> None:
        """Test listing variants in empty directory."""
        loader = create_template_loader(tmp_path)
        variants = loader.list_variants()
        assert variants == []

    def test_load_variant_prefers_jinja2_extensions(self, tmp_path: Path) -> None:
        """Test that jinja2 extensions are preferred over .md."""
        variant_dir = tmp_path / "variant"
        variant_dir.mkdir()

        # Create multiple files with same base name but different extensions
        (variant_dir / "test.md").write_text("plain markdown")
        (variant_dir / "test.md.jinja2").write_text("jinja2 template")

        loader = create_template_loader(tmp_path)
        content = loader.load_variant_template("test")

        # Should load .md.jinja2 first (checked before .md)
        assert content == "jinja2 template"
