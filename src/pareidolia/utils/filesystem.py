"""File system utilities for pareidolia."""

from pathlib import Path


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
