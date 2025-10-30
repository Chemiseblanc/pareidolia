"""File system utilities for pareidolia."""

import urllib.error
import urllib.request
from abc import abstractmethod
from pathlib import Path
from typing import Protocol
from urllib.parse import urlparse

GITHUB_REQUEST_TIMEOUT = 5  # Timeout for GitHub API requests in seconds


class FileSystem(Protocol):
    """Protocol for filesystem abstraction supporting local and remote sources."""

    @abstractmethod
    def read_file(self, path: str) -> str:
        """Read file content.

        Args:
            path: Path to the file relative to filesystem root

        Returns:
            File content as string

        Raises:
            FileNotFoundError: If file does not exist
            IOError: If file cannot be read
        """
        ...

    @abstractmethod
    def list_files(self, path: str, pattern: str) -> list[str]:
        """List files matching pattern in directory.

        Args:
            path: Directory path relative to filesystem root
            pattern: Glob pattern to match files

        Returns:
            List of matching file paths (relative to filesystem root)

        Raises:
            FileNotFoundError: If directory does not exist
        """
        ...

    @abstractmethod
    def exists(self, path: str) -> bool:
        """Check if file or directory exists.

        Args:
            path: Path to check relative to filesystem root

        Returns:
            True if path exists, False otherwise
        """
        ...

    @abstractmethod
    def is_readonly(self) -> bool:
        """Check if filesystem is read-only.

        Returns:
            True if filesystem is read-only, False if writable
        """
        ...


class LocalFileSystem:
    """Local filesystem implementation."""

    def __init__(self, base_path: Path) -> None:
        """Initialize with base directory path.

        Args:
            base_path: Base directory for all file operations
        """
        self.base_path = base_path

    def read_file(self, path: str) -> str:
        """Read file content from local filesystem.

        Args:
            path: Path to file relative to base_path

        Returns:
            File content as string

        Raises:
            FileNotFoundError: If file does not exist
            IOError: If file cannot be read
        """
        full_path = self.base_path / path
        return read_file(full_path)

    def list_files(self, path: str, pattern: str) -> list[str]:
        """List files matching pattern in directory.

        Args:
            path: Directory path relative to base_path
            pattern: Glob pattern to match files

        Returns:
            List of matching file paths relative to base_path

        Raises:
            FileNotFoundError: If directory does not exist
        """
        full_path = self.base_path / path
        matched_files = find_files(full_path, pattern)
        # Convert to relative paths as strings
        return [str(f.relative_to(self.base_path)) for f in matched_files]

    def exists(self, path: str) -> bool:
        """Check if file exists.

        Args:
            path: Path to check relative to base_path

        Returns:
            True if path exists, False otherwise
        """
        full_path = self.base_path / path
        return full_path.exists()

    def is_readonly(self) -> bool:
        """Local filesystem is writable.

        Returns:
            False (local filesystem is writable)
        """
        return False


class GitHubFileSystem:
    """GitHub repository filesystem (read-only, in-memory)."""

    def __init__(
        self, org: str, repo: str, ref: str = "main", subpath: str = ""
    ) -> None:
        """Initialize GitHub filesystem.

        Args:
            org: GitHub organization or user
            repo: Repository name
            ref: Branch, tag, or commit SHA (defaults to "main")
            subpath: Optional subdirectory path within repo
        """
        self.org = org
        self.repo = repo
        self.ref = ref
        self.subpath = subpath.rstrip("/")
        self._cache: dict[str, str] = {}  # In-memory file cache

    def _build_url(self, path: str) -> str:
        """Build raw.githubusercontent.com URL.

        Args:
            path: Path to file within repository

        Returns:
            Full URL to raw file content
        """
        # Remove leading slash if present
        path = path.lstrip("/")

        # Build URL components
        parts = [
            "https://raw.githubusercontent.com",
            self.org,
            self.repo,
            self.ref,
        ]

        # Add subpath if specified
        if self.subpath:
            parts.append(self.subpath)

        # Add file path
        parts.append(path)

        return "/".join(parts)

    def read_file(self, path: str) -> str:
        """Fetch file from GitHub (with caching).

        Args:
            path: Path to file relative to filesystem root

        Returns:
            File content as string

        Raises:
            FileNotFoundError: If file does not exist (404)
            IOError: If file cannot be fetched (network errors, etc.)
        """
        # Check cache first
        if path in self._cache:
            return self._cache[path]

        # Build URL and fetch content
        url = self._build_url(path)

        try:
            with urllib.request.urlopen(
                url, timeout=GITHUB_REQUEST_TIMEOUT
            ) as response:
                content: str = response.read().decode("utf-8")
                # Cache the result
                self._cache[path] = content
                return content
        except urllib.error.HTTPError as e:
            if e.code == 404:
                github_path = f"{self.org}/{self.repo}/{self.ref}/{path}"
                raise FileNotFoundError(
                    f"File not found on GitHub: {github_path}"
                ) from e
            raise OSError(
                f"Failed to fetch file from GitHub (HTTP {e.code}): {url}"
            ) from e
        except urllib.error.URLError as e:
            raise OSError(f"Network error fetching file from GitHub: {url}") from e
        except Exception as e:
            raise OSError(f"Error reading file from GitHub: {url}") from e

    def list_files(self, path: str, pattern: str) -> list[str]:
        """List files - not fully supported for GitHub, returns empty list.

        GitHub API doesn't support directory listing via raw URLs.
        Files are accessed on-demand, so templates must be explicitly
        referenced in configuration.

        Args:
            path: Directory path (ignored)
            pattern: Glob pattern (ignored)

        Returns:
            Empty list (directory listing not supported)
        """
        return []

    def exists(self, path: str) -> bool:
        """Check if file exists by attempting to fetch it.

        Args:
            path: Path to check relative to filesystem root

        Returns:
            True if file exists and is accessible, False otherwise
        """
        try:
            self.read_file(path)
            return True
        except (OSError, FileNotFoundError):
            return False

    def is_readonly(self) -> bool:
        """GitHub filesystem is read-only.

        Returns:
            True (GitHub filesystem is read-only)
        """
        return True


def read_file(path: Path) -> str:
    """Read and return the contents of a file.

    Args:
        path: Path to the file to read

    Returns:
        The file contents as a string

    Raises:
        FileNotFoundError: If the file does not exist
        IOError: If the file cannot be read
    """
    return path.read_text(encoding="utf-8")


def write_file(path: Path, content: str) -> None:
    """Write content to a file.

    Args:
        path: Path to the file to write
        content: Content to write to the file

    Raises:
        IOError: If the file cannot be written
    """
    path.write_text(content, encoding="utf-8")


def ensure_directory(path: Path) -> None:
    """Ensure a directory exists, creating it if necessary.

    Args:
        path: Path to the directory

    Raises:
        IOError: If the directory cannot be created
    """
    path.mkdir(parents=True, exist_ok=True)


def find_files(directory: Path, pattern: str) -> list[Path]:
    """Find files matching a pattern in a directory.

    Args:
        directory: Directory to search
        pattern: Glob pattern to match

    Returns:
        List of matching file paths

    Raises:
        FileNotFoundError: If the directory does not exist
    """
    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")

    return sorted(directory.glob(pattern))


def parse_source_uri(source_uri: str) -> FileSystem:
    """Parse a source URI and return the appropriate FileSystem implementation.

    Supported formats:
    - Local path: "/path/to/project" or "./relative/path"
    - File URI: "file:///absolute/path" or "file://./relative/path"
    - GitHub URI: "github://org/repo[@ref][/subpath]"

    Args:
        source_uri: Source URI string

    Returns:
        FileSystem implementation (LocalFileSystem or GitHubFileSystem)

    Raises:
        ValueError: If URI scheme is unsupported or format is invalid
    """
    parsed = urlparse(source_uri)
    scheme = parsed.scheme

    # No scheme (bare path) - treat as local path
    if not scheme:
        return LocalFileSystem(Path(source_uri))

    # file:// prefix - strip and treat as local path
    if scheme == "file":
        path = parsed.path
        return LocalFileSystem(Path(path))

    # github:// URL - delegate to GitHub filesystem factory
    if scheme == "github":
        # Import here to avoid circular dependency
        from pareidolia.utils.github import create_github_filesystem
        return create_github_filesystem(source_uri)

    # Unsupported scheme
    raise ValueError(
        f"Unsupported URI scheme: '{scheme}'. "
        f"Supported schemes are: file://, github://, or bare paths"
    )
