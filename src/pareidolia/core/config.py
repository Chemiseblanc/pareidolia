"""Configuration management for pareidolia."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore

from pareidolia.core.exceptions import ConfigurationError, ValidationError
from pareidolia.core.models import ExportConfig, VariantConfig
from pareidolia.utils.validation import validate_config_schema


@dataclass(frozen=True)
class PareidoliaConfig:
    """Complete configuration for pareidolia.

    Attributes:
        root: Root directory containing persona/action/example folders
        export: Export configuration
        variants: Optional variant generation configuration
    """

    root: Path
    export: ExportConfig
    variants: VariantConfig | None = None

    @classmethod
    def from_file(cls, config_path: Path) -> "PareidoliaConfig":
        """Load configuration from a TOML file.

        Args:
            config_path: Path to the configuration file

        Returns:
            Loaded configuration

        Raises:
            ConfigurationError: If the configuration cannot be loaded or is invalid
        """
        if not config_path.exists():
            raise ConfigurationError(f"Configuration file not found: {config_path}")

        try:
            with open(config_path, "rb") as f:
                config_data = tomllib.load(f)
        except Exception as e:
            raise ConfigurationError(
                f"Failed to parse configuration file: {config_path}"
            ) from e

        return cls.from_dict(config_data, config_path.parent)

    @classmethod
    def from_dict(
        cls, config_data: dict[str, Any], base_path: Path
    ) -> "PareidoliaConfig":
        """Create configuration from a dictionary.

        Args:
            config_data: Configuration dictionary
            base_path: Base path for resolving relative paths

        Returns:
            Configuration object

        Raises:
            ConfigurationError: If the configuration is invalid
        """
        try:
            validate_config_schema(config_data)
        except Exception as e:
            raise ConfigurationError(f"Invalid configuration schema: {e}") from e

        # Parse pareidolia section
        pareidolia = config_data.get("pareidolia", {})
        root_str = pareidolia.get("root", "pareidolia")
        root = base_path / root_str

        # Parse export section
        export_data = config_data.get("export", {})
        tool = export_data.get("tool", "standard")
        library = export_data.get("library")
        output_dir_str = export_data.get("output_dir", "prompts")
        output_dir = base_path / output_dir_str

        try:
            export = ExportConfig(
                tool=tool,
                library=library,
                output_dir=output_dir,
            )
        except ValueError as e:
            raise ConfigurationError(f"Invalid export configuration: {e}") from e

        # Parse variants section (optional)
        variants_data = config_data.get("variants")
        variants: VariantConfig | None = None
        if variants_data:
            try:
                variants = VariantConfig(
                    persona=variants_data["persona"],
                    action=variants_data["action"],
                    generate=variants_data["generate"],
                    cli_tool=variants_data.get("cli_tool"),
                )
            except (KeyError, ValueError, ValidationError) as e:
                raise ConfigurationError(
                    f"Invalid variants configuration: {e}"
                ) from e

        return cls(root=root, export=export, variants=variants)

    @classmethod
    def from_defaults(
        cls,
        project_root: Path | None = None,
        tool: str = "standard",
        library: str | None = None,
        output_dir: str = "prompts",
    ) -> "PareidoliaConfig":
        """Create configuration with default values.

        Args:
            project_root: Project root directory (defaults to current directory)
            tool: Target tool name
            library: Optional library name
            output_dir: Output directory (relative to project_root)

        Returns:
            Configuration with defaults
        """
        if project_root is None:
            project_root = Path.cwd()

        root = project_root / "pareidolia"
        output_path = project_root / output_dir
        export = ExportConfig(tool=tool, library=library, output_dir=output_path)

        return cls(root=root, export=export, variants=None)

    def merge_overrides(
        self,
        tool: str | None = None,
        library: str | None = None,
        output_dir: str | None = None,
    ) -> "PareidoliaConfig":
        """Create a new configuration with CLI overrides applied.

        Args:
            tool: Override tool setting
            library: Override library setting
            output_dir: Override output directory (relative to config location)

        Returns:
            New configuration with overrides applied
        """
        # Resolve output_dir override relative to root's parent (project root)
        if output_dir is not None:
            output_path = self.root.parent / output_dir
        else:
            output_path = self.export.output_dir

        export = ExportConfig(
            tool=tool if tool is not None else self.export.tool,
            library=library if library is not None else self.export.library,
            output_dir=output_path,
        )

        return PareidoliaConfig(root=self.root, export=export, variants=self.variants)
