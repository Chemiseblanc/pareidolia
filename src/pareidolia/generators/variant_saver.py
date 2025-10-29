"""Variant saver for persisting cached variants as action templates."""

from pathlib import Path

from pareidolia.generators.variant_cache import CachedVariant
from pareidolia.templates.loader import TemplateLoader
from pareidolia.utils.filesystem import ensure_directory, write_file


class VariantSaver:
    """Saves cached variants as action templates for future reuse.

    This class converts AI-generated variants back into Jinja2 templates
    by replacing persona content with {{ persona }} placeholders.

    Attributes:
        project_root: Root directory of the project
        _loader: Template loader for accessing persona content
    """

    def __init__(self, project_root: Path) -> None:
        """Initialize the variant saver.

        Args:
            project_root: Root directory of the project
        """
        self.project_root = project_root
        self._loader = TemplateLoader(project_root / "pareidolia")

    def save_variant(
        self, cached_variant: CachedVariant, force: bool = False
    ) -> tuple[Path, bool, str | None]:
        """Save a cached variant as an action template.

        Args:
            cached_variant: The cached variant to save
            force: If True, overwrite existing files

        Returns:
            Tuple of (file_path, was_saved, error_message)
            - file_path: Path where the file would be/was saved
            - was_saved: True if file was written, False if skipped
            - error_message: Error message if failed, None if successful
        """
        # Get the target path
        file_path = self._get_template_path(
            cached_variant.variant_name, cached_variant.action_name
        )

        # Check if file exists and force is False
        if file_path.exists() and not force:
            return (file_path, False, "File exists")

        # Load persona content for template conversion
        try:
            persona = self._loader.load_persona(cached_variant.persona_name)
            template_content = self._convert_to_template(
                cached_variant.content, persona.content
            )
        except Exception as e:
            return (file_path, False, f"Failed to convert template: {e}")

        # Ensure directory exists
        try:
            ensure_directory(file_path.parent)
        except Exception as e:
            return (file_path, False, f"Failed to create directory: {e}")

        # Write the file
        try:
            write_file(file_path, template_content)
            return (file_path, True, None)
        except Exception as e:
            return (file_path, False, f"Failed to write file: {e}")

    def save_all(
        self, cached_variants: list[CachedVariant], force: bool = False
    ) -> dict[Path, tuple[bool, str | None]]:
        """Save multiple cached variants.

        Args:
            cached_variants: List of cached variants to save
            force: If True, overwrite existing files

        Returns:
            Dictionary mapping file paths to (was_saved, error_message) tuples
        """
        results: dict[Path, tuple[bool, str | None]] = {}

        for variant in cached_variants:
            file_path, was_saved, error_msg = self.save_variant(variant, force)
            results[file_path] = (was_saved, error_msg)

        return results

    def _convert_to_template(self, content: str, persona_content: str) -> str:
        """Convert variant content to template format.

        Replaces the persona content with {{ persona }} placeholder.

        Args:
            content: The variant content to convert
            persona_content: The persona content to replace

        Returns:
            Template content with persona placeholder
        """
        # Simple string replacement - if persona content is found, replace it
        # If not found, return content as-is (may already be a template)
        if persona_content in content:
            return content.replace(persona_content, "{{ persona }}")
        return content

    def _get_template_path(self, variant_name: str, action_name: str) -> Path:
        """Get the path for a template file.

        Args:
            variant_name: The variant name
            action_name: The action name

        Returns:
            Path to the template file
        """
        action_dir = self.project_root / "pareidolia" / "action"
        return action_dir / f"{variant_name}-{action_name}.md.j2"
