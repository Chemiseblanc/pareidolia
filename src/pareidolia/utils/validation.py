"""Validation utilities for pareidolia."""

import re
from pathlib import Path
from typing import Any

from pareidolia.core.exceptions import ValidationError


def validate_identifier(name: str, field_name: str = "identifier") -> None:
    """Validate an identifier (persona name, action name, etc.).

    Identifiers must:
    - Not be empty
    - Contain only lowercase letters, numbers, hyphens, and underscores
    - Start with a letter
    - Not end with a hyphen or underscore

    Args:
        name: The identifier to validate
        field_name: The name of the field being validated (for error messages)

    Raises:
        ValidationError: If the identifier is invalid
    """
    if not name or not name.strip():
        raise ValidationError(f"{field_name} cannot be empty")

    name = name.strip()

    # Must start with a letter
    if not name[0].isalpha():
        raise ValidationError(
            f"{field_name} must start with a letter: {name}"
        )

    # Must contain only valid characters
    if not re.match(r"^[a-z0-9_-]+$", name):
        raise ValidationError(
            f"{field_name} must contain only lowercase letters, numbers, "
            f"hyphens, and underscores: {name}"
        )

    # Must not end with hyphen or underscore
    if name.endswith(("-", "_")):
        raise ValidationError(
            f"{field_name} must not end with a hyphen or underscore: {name}"
        )


def validate_path(path: Path, must_exist: bool = False) -> None:
    """Validate a file path.

    Args:
        path: The path to validate
        must_exist: If True, the path must exist

    Raises:
        ValidationError: If the path is invalid
    """
    if must_exist and not path.exists():
        raise ValidationError(f"Path does not exist: {path}")

    # Check if path is absolute or can be resolved
    try:
        path.resolve()
    except (OSError, RuntimeError) as e:
        raise ValidationError(f"Invalid path: {path}") from e


def validate_directory(path: Path, must_exist: bool = False) -> None:
    """Validate a directory path.

    Args:
        path: The directory path to validate
        must_exist: If True, the directory must exist

    Raises:
        ValidationError: If the directory is invalid
    """
    validate_path(path, must_exist=must_exist)

    if path.exists() and not path.is_dir():
        raise ValidationError(f"Path is not a directory: {path}")


def validate_config_schema(config: dict[str, Any]) -> None:
    """Validate the schema of a configuration dictionary.

    Args:
        config: The configuration dictionary to validate

    Raises:
        ValidationError: If the configuration schema is invalid
    """
    if not isinstance(config, dict):
        raise ValidationError("Configuration must be a dictionary")

    # Check for pareidolia section
    if "pareidolia" in config:
        pareidolia = config["pareidolia"]
        if not isinstance(pareidolia, dict):
            raise ValidationError("pareidolia section must be a dictionary")

        # Validate root if present
        if "root" in pareidolia and not isinstance(pareidolia["root"], str):
            raise ValidationError("pareidolia.root must be a string")

    # Check for export section
    if "export" in config:
        export = config["export"]
        if not isinstance(export, dict):
            raise ValidationError("export section must be a dictionary")

        # Validate tool if present
        if "tool" in export and not isinstance(export["tool"], str):
            raise ValidationError("export.tool must be a string")

        # Validate library if present
        if (
            "library" in export
            and export["library"] is not None
            and not isinstance(export["library"], str)
        ):
            raise ValidationError("export.library must be a string or null")

        # Validate output_dir if present
        if "output_dir" in export and not isinstance(export["output_dir"], str):
            raise ValidationError("export.output_dir must be a string")
