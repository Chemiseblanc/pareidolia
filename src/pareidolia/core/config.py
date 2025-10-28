"""Configuration management for pareidolia."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore

from pareidolia.core.exceptions import ConfigurationError, ValidationError
from pareidolia.core.models import GenerateConfig, PromptConfig
from pareidolia.utils.validation import validate_config_schema


@dataclass(frozen=True)
class PareidoliaConfig:
    """Complete configuration for pareidolia.

    Attributes:
        root: Root directory containing persona/action/example folders
        generate: Generate configuration
        metadata: Global metadata dictionary (merged with per-prompt metadata)
        prompt: List of prompt variant generation configurations
    """

    root: Path
    generate: GenerateConfig
    metadata: dict[str, Any]
    prompt: list[PromptConfig] = field(default_factory=list)

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

        # Parse generate section
        generate_data = config_data.get("generate", {})
        tool = generate_data.get("tool", "standard")
        library = generate_data.get("library")
        output_dir_str = generate_data.get("output_dir", "prompts")
        output_dir = base_path / output_dir_str

        try:
            generate = GenerateConfig(
                tool=tool,
                library=library,
                output_dir=output_dir,
            )
        except ValueError as e:
            raise ConfigurationError(f"Invalid generate configuration: {e}") from e

        # Parse global metadata section (optional)
        global_metadata = config_data.get("metadata", {})
        if not isinstance(global_metadata, dict):
            raise ConfigurationError("metadata section must be a dictionary")

        # Parse prompt array (optional)
        prompt_data_list = config_data.get("prompt", [])
        prompts: list[PromptConfig] = []

        if not isinstance(prompt_data_list, list):
            raise ConfigurationError("prompt section must be an array of tables")

        for idx, prompt_data in enumerate(prompt_data_list):
            if not isinstance(prompt_data, dict):
                raise ConfigurationError(
                    f"prompt[{idx}] must be a table/dictionary"
                )

            try:
                # Extract per-prompt metadata, default to empty dict
                prompt_metadata = prompt_data.get("metadata", {})

                # Merge global and per-prompt metadata (per-prompt overrides global)
                merged_metadata = {**global_metadata, **prompt_metadata}

                prompts.append(
                    PromptConfig(
                        persona=prompt_data["persona"],
                        action=prompt_data["action"],
                        variants=prompt_data["variants"],
                        cli_tool=prompt_data.get("cli_tool"),
                        metadata=merged_metadata,
                    )
                )
            except (KeyError, ValueError, ValidationError) as e:
                raise ConfigurationError(
                    f"Invalid prompt[{idx}] configuration: {e}"
                ) from e

        return cls(
            root=root,
            generate=generate,
            metadata=global_metadata,
            prompt=prompts,
        )

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
        generate = GenerateConfig(tool=tool, library=library, output_dir=output_path)

        return cls(root=root, generate=generate, metadata={}, prompt=[])

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
            output_path = self.generate.output_dir

        generate = GenerateConfig(
            tool=tool if tool is not None else self.generate.tool,
            library=library if library is not None else self.generate.library,
            output_dir=output_path,
        )

        return PareidoliaConfig(
            root=self.root,
            generate=generate,
            metadata=self.metadata,
            prompt=self.prompt,
        )
