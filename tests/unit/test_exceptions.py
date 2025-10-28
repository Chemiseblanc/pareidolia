"""Unit tests for exception hierarchy."""

import pytest

from pareidolia.core.exceptions import (
    ActionNotFoundError,
    CLIToolError,
    ConfigurationError,
    NoAvailableCLIToolError,
    PareidoliaError,
    PersonaNotFoundError,
    TemplateRenderError,
    ValidationError,
    VariantError,
    VariantTemplateNotFoundError,
)


def test_base_exception_inheritance() -> None:
    """Test that all exceptions inherit from PareidoliaError."""
    assert issubclass(ConfigurationError, PareidoliaError)
    assert issubclass(PersonaNotFoundError, PareidoliaError)
    assert issubclass(ActionNotFoundError, PareidoliaError)
    assert issubclass(TemplateRenderError, PareidoliaError)
    assert issubclass(ValidationError, PareidoliaError)
    assert issubclass(VariantError, PareidoliaError)
    assert issubclass(VariantTemplateNotFoundError, PareidoliaError)
def test_exception_messages() -> None:
    """Test that exceptions can be raised with custom messages."""
    msg = "Test error message"

    exc = PareidoliaError(msg)
    assert str(exc) == msg

    exc = ConfigurationError(msg)
    assert str(exc) == msg

    exc = PersonaNotFoundError(msg)
    assert str(exc) == msg

    exc = ActionNotFoundError(msg)
    assert str(exc) == msg

    exc = TemplateRenderError(msg)
    assert str(exc) == msg

    exc = ValidationError(msg)
    assert str(exc) == msg

    exc = VariantError(msg)
def test_exceptions_can_be_caught_as_base() -> None:
    """Test that specific exceptions can be caught as PareidoliaError."""
    with pytest.raises(PareidoliaError):
        raise ConfigurationError("test")

    with pytest.raises(PareidoliaError):
        raise PersonaNotFoundError("test")

    with pytest.raises(PareidoliaError):
        raise ActionNotFoundError("test")

    with pytest.raises(PareidoliaError):
        raise TemplateRenderError("test")

    with pytest.raises(PareidoliaError):
        raise ValidationError("test")

    with pytest.raises(PareidoliaError):
        raise VariantError("test")

    with pytest.raises(PareidoliaError):
        raise VariantTemplateNotFoundError("test")

    with pytest.raises(PareidoliaError):
        raise CLIToolError("test")

    with pytest.raises(PareidoliaError):
        raise NoAvailableCLIToolError("test")


def test_variant_exceptions_inherit_from_variant_error() -> None:
    """Test that variant exceptions inherit from VariantError."""
    assert issubclass(VariantTemplateNotFoundError, VariantError)
    assert issubclass(CLIToolError, VariantError)
    assert issubclass(NoAvailableCLIToolError, VariantError)

