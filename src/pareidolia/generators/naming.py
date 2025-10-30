"""Naming convention strategies for different tools."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import ClassVar, Protocol


class NamingConvention(Protocol):
    """Protocol for naming convention strategies."""

    def get_filename(self, action_name: str, library: str | None = None) -> str:
        """Generate a filename for an action.

        Args:
            action_name: The action name
            library: Optional library name

        Returns:
            The generated filename
        """
        ...

    def get_output_path(
        self,
        output_dir: Path,
        action_name: str,
        library: str | None = None,
    ) -> Path:
        """Generate the full output path for an action.

        Args:
            output_dir: The base output directory
            action_name: The action name
            library: Optional library name

        Returns:
            The complete output path
        """
        ...


class ToolAdapter(ABC):
    """Base class for tool-specific naming adapters with auto-registration.

    Concrete subclasses are automatically registered in the class-level
    registry when they are defined, enabling dynamic tool discovery.

    This class also satisfies the NamingConvention Protocol through its
    abstract methods get_filename() and get_output_path().
    """

    _registry: ClassVar[dict[str, "ToolAdapter"]] = {}

    def __init_subclass__(cls, auto_register: bool = True, **kwargs: object) -> None:
        """Register adapter subclasses automatically.

        Args:
            auto_register: Whether to register this class (default: True)
            **kwargs: Additional keyword arguments for super().__init_subclass__
        """
        super().__init_subclass__(**kwargs)
        if auto_register:
            instance = cls()
            cls._registry[instance.name] = instance

    @property
    @abstractmethod
    def name(self) -> str:
        """Get the tool identifier.

        Returns:
            The tool name (e.g., 'copilot', 'claude-code')
        """
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Get a human-readable description of this tool format.

        Returns:
            Description of the tool's naming convention
        """
        ...

    @property
    @abstractmethod
    def file_extension(self) -> str:
        """Get the file extension for this tool's format.

        Returns:
            File extension including the dot (e.g., '.prompt.md')
        """
        ...

    @classmethod
    def get_adapter(cls, name: str) -> "ToolAdapter":
        """Get an adapter by name.

        Args:
            name: The tool name

        Returns:
            The registered adapter instance

        Raises:
            ValueError: If the tool name is not recognized
        """
        if name not in cls._registry:
            available = ", ".join(sorted(cls._registry.keys()))
            raise ValueError(f"Unknown tool '{name}'. Available: {available}")
        return cls._registry[name]

    @classmethod
    def list_available(cls) -> dict[str, "ToolAdapter"]:
        """Get all registered adapters.

        Returns:
            Dictionary mapping tool names to adapter instances
        """
        return cls._registry.copy()

    @classmethod
    def is_supported(cls, name: str) -> bool:
        """Check if a tool name is supported.

        Args:
            name: The tool name to check

        Returns:
            True if the tool is registered, False otherwise
        """
        return name in cls._registry

    @classmethod
    def _clear_registry(cls) -> None:
        """Clear the adapter registry.

        This method is primarily for testing purposes to ensure clean state
        between test runs.
        """
        cls._registry.clear()

    @abstractmethod
    def get_filename(self, action_name: str, library: str | None = None) -> str:
        """Generate a filename for an action.

        Args:
            action_name: The action name
            library: Optional library name

        Returns:
            The generated filename
        """
        ...

    @abstractmethod
    def get_output_path(
        self,
        output_dir: Path,
        action_name: str,
        library: str | None = None,
    ) -> Path:
        """Generate the full output path for an action.

        Args:
            output_dir: The base output directory
            action_name: The action name
            library: Optional library name

        Returns:
            The complete output path
        """
        ...


class StandardNaming(ToolAdapter):
    """Standard naming convention: <action>.prompt.md."""

    @property
    def name(self) -> str:
        """Get the tool identifier.

        Returns:
            The tool name 'standard'
        """
        return "standard"

    @property
    def description(self) -> str:
        """Get a human-readable description.

        Returns:
            Description of the standard naming format
        """
        return "Standard format (.prompt.md)"

    @property
    def file_extension(self) -> str:
        """Get the file extension.

        Returns:
            The standard file extension
        """
        return ".prompt.md"

    def get_filename(self, action_name: str, library: str | None = None) -> str:
        """Generate a filename using standard convention.

        Args:
            action_name: The action name
            library: Optional library name (ignored for standard naming)

        Returns:
            Filename in format: <action>.prompt.md
        """
        return f"{action_name}.prompt.md"

    def get_output_path(
        self,
        output_dir: Path,
        action_name: str,
        library: str | None = None,
    ) -> Path:
        """Generate the full output path.

        Args:
            output_dir: The base output directory
            action_name: The action name
            library: Optional library name (ignored)

        Returns:
            Path to output file
        """
        filename = self.get_filename(action_name, library)
        return output_dir / filename


class CopilotNaming(ToolAdapter):
    """GitHub Copilot library naming: flat with prefix.

    Format: <library>.<action>.prompt.md
    """

    @property
    def name(self) -> str:
        """Get the tool identifier.

        Returns:
            The tool name 'copilot'
        """
        return "copilot"

    @property
    def description(self) -> str:
        """Get a human-readable description.

        Returns:
            Description of the Copilot naming format
        """
        return "GitHub Copilot format (.prompt.md)"

    @property
    def file_extension(self) -> str:
        """Get the file extension.

        Returns:
            The Copilot file extension
        """
        return ".prompt.md"

    def get_filename(self, action_name: str, library: str | None = None) -> str:
        """Generate a filename using Copilot convention.

        Args:
            action_name: The action name
            library: Optional library name

        Returns:
            Filename in format: <library>.<action>.prompt.md or <action>.prompt.md
        """
        if library:
            return f"{library}.{action_name}.prompt.md"
        return f"{action_name}.prompt.md"

    def get_output_path(
        self,
        output_dir: Path,
        action_name: str,
        library: str | None = None,
    ) -> Path:
        """Generate the full output path.

        Args:
            output_dir: The base output directory
            action_name: The action name
            library: Optional library name

        Returns:
            Path to output file (flat structure)
        """
        filename = self.get_filename(action_name, library)
        return output_dir / filename


class ClaudeCodeNaming(ToolAdapter):
    """Claude Code library naming: subdirectory structure.

    Format: <library>/<action>.md
    """

    @property
    def name(self) -> str:
        """Get the tool identifier.

        Returns:
            The tool name 'claude-code'
        """
        return "claude-code"

    @property
    def description(self) -> str:
        """Get a human-readable description.

        Returns:
            Description of the Claude Code naming format
        """
        return "Claude Code format (.md)"

    @property
    def file_extension(self) -> str:
        """Get the file extension.

        Returns:
            The Claude Code file extension
        """
        return ".md"

    def get_filename(self, action_name: str, library: str | None = None) -> str:
        """Generate a filename using Claude Code convention.

        Args:
            action_name: The action name
            library: Optional library name (used for subdirectory)

        Returns:
            Filename in format: <action>.md
        """
        return f"{action_name}.md"

    def get_output_path(
        self,
        output_dir: Path,
        action_name: str,
        library: str | None = None,
    ) -> Path:
        """Generate the full output path.

        Args:
            output_dir: The base output directory
            action_name: The action name
            library: Optional library name (creates subdirectory)

        Returns:
            Path to output file in subdirectory structure
        """
        filename = self.get_filename(action_name, library)
        if library:
            return output_dir / library / filename
        return output_dir / filename
