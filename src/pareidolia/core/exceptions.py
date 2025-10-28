"""Custom exceptions for pareidolia."""


class PareidoliaError(Exception):
    """Base exception for all pareidolia errors."""


class ConfigurationError(PareidoliaError):
    """Raised when configuration is invalid or cannot be loaded."""


class PersonaNotFoundError(PareidoliaError):
    """Raised when a persona file cannot be found."""


class ActionNotFoundError(PareidoliaError):
    """Raised when an action template cannot be found."""


class TemplateRenderError(PareidoliaError):
    """Raised when template rendering fails."""


class ValidationError(PareidoliaError):
    """Raised when input validation fails."""


class VariantError(PareidoliaError):
    """Base exception for variant generation."""


class VariantTemplateNotFoundError(VariantError):
    """Raised when variant template cannot be found."""


class CLIToolError(VariantError):
    """Raised when CLI tool invocation fails."""


class NoAvailableCLIToolError(VariantError):
    """Raised when no CLI tools are available."""
