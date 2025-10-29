"""Unit tests for validation utilities."""

import pytest

from pareidolia.core.exceptions import ValidationError
from pareidolia.utils.validation import (
    validate_config_schema,
    validate_identifier,
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
            "generate": {
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

    def test_invalid_generate_section(self) -> None:
        """Test that invalid generate section fails validation."""
        with pytest.raises(ValidationError):
            validate_config_schema({"generate": "not a dict"})

    def test_invalid_tool_type(self) -> None:
        """Test that invalid tool type fails validation."""
        with pytest.raises(ValidationError, match="tool must be a string"):
            validate_config_schema({"generate": {"tool": 123}})

    def test_invalid_library_type(self) -> None:
        """Test that invalid library type fails validation."""
        with pytest.raises(ValidationError, match="library must be a string"):
            validate_config_schema({"generate": {"library": 123}})

    def test_null_library_allowed(self) -> None:
        """Test that null library value is allowed."""
        config = {"generate": {"library": None}}
        validate_config_schema(config)  # Should not raise
