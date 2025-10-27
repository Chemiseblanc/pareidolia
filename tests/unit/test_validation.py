"""Unit tests for validation utilities."""

from pathlib import Path

import pytest

from pareidolia.core.exceptions import ValidationError
from pareidolia.utils.validation import (
    validate_config_schema,
    validate_directory,
    validate_identifier,
    validate_path,
)


class TestValidateIdentifier:
    """Tests for identifier validation."""

    @pytest.mark.parametrize("valid_name", [
        "researcher",
        "research-assistant",
        "test_persona",
        "v1",
        "test-123",
        "a",
    ])
    def test_valid_identifiers(self, valid_name: str) -> None:
        """Test that valid identifiers pass validation."""
        validate_identifier(valid_name)  # Should not raise

    @pytest.mark.parametrize("invalid_name,reason", [
        ("", "empty"),
        ("  ", "whitespace only"),
        ("123test", "starts with number"),
        ("-test", "starts with hyphen"),
        ("_test", "starts with underscore"),
        ("test-", "ends with hyphen"),
        ("test_", "ends with underscore"),
        ("Test", "uppercase letter"),
        ("test name", "space"),
        ("test@name", "special character"),
    ])
    def test_invalid_identifiers(self, invalid_name: str, reason: str) -> None:
        """Test that invalid identifiers raise ValidationError."""
        with pytest.raises(ValidationError):
            validate_identifier(invalid_name)


class TestValidatePath:
    """Tests for path validation."""

    def test_validate_existing_path(self, temp_dir: Path) -> None:
        """Test validation of an existing path."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("test")

        validate_path(test_file, must_exist=True)  # Should not raise

    def test_validate_nonexistent_path_not_required(self, temp_dir: Path) -> None:
        """Test validation of non-existent path when not required to exist."""
        test_file = temp_dir / "nonexistent.txt"
        validate_path(test_file, must_exist=False)  # Should not raise

    def test_validate_nonexistent_path_required(self, temp_dir: Path) -> None:
        """Test that validation fails for non-existent path when required."""
        test_file = temp_dir / "nonexistent.txt"

        with pytest.raises(ValidationError, match="does not exist"):
            validate_path(test_file, must_exist=True)


class TestValidateDirectory:
    """Tests for directory validation."""

    def test_validate_existing_directory(self, temp_dir: Path) -> None:
        """Test validation of an existing directory."""
        validate_directory(temp_dir, must_exist=True)  # Should not raise

    def test_validate_nonexistent_directory_not_required(self, temp_dir: Path) -> None:
        """Test validation of non-existent directory when not required."""
        test_dir = temp_dir / "nonexistent"
        validate_directory(test_dir, must_exist=False)  # Should not raise

    def test_validate_file_as_directory(self, temp_dir: Path) -> None:
        """Test that validation fails when path is a file, not a directory."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("test")

        with pytest.raises(ValidationError, match="not a directory"):
            validate_directory(test_file, must_exist=True)


class TestValidateConfigSchema:
    """Tests for configuration schema validation."""

    def test_valid_empty_config(self) -> None:
        """Test that empty config is valid."""
        validate_config_schema({})  # Should not raise

    def test_valid_full_config(self) -> None:
        """Test that valid full config passes validation."""
        config = {
            "pareidolia": {
                "root": "pareidolia",
            },
            "export": {
                "tool": "copilot",
                "library": "mylib",
                "output_dir": "output",
            },
        }
        validate_config_schema(config)  # Should not raise

    def test_invalid_config_not_dict(self) -> None:
        """Test that non-dict config fails validation."""
        with pytest.raises(ValidationError, match="must be a dictionary"):
            validate_config_schema("not a dict")  # type: ignore

    def test_invalid_pareidolia_section(self) -> None:
        """Test that invalid pareidolia section fails validation."""
        with pytest.raises(ValidationError):
            validate_config_schema({"pareidolia": "not a dict"})

    def test_invalid_export_section(self) -> None:
        """Test that invalid export section fails validation."""
        with pytest.raises(ValidationError):
            validate_config_schema({"export": "not a dict"})

    def test_invalid_tool_type(self) -> None:
        """Test that invalid tool type fails validation."""
        with pytest.raises(ValidationError, match="tool must be a string"):
            validate_config_schema({"export": {"tool": 123}})

    def test_invalid_library_type(self) -> None:
        """Test that invalid library type fails validation."""
        with pytest.raises(ValidationError, match="library must be a string"):
            validate_config_schema({"export": {"library": 123}})

    def test_null_library_allowed(self) -> None:
        """Test that null library value is allowed."""
        config = {"export": {"library": None}}
        validate_config_schema(config)  # Should not raise
