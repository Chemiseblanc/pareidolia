"""GitHub repository access utilities."""
import re
from typing import NamedTuple

from pareidolia.core.exceptions import PareidoliaError
from pareidolia.utils.filesystem import GitHubFileSystem


class GitHubURL(NamedTuple):
    """Parsed GitHub repository URL."""

    org: str
    repo: str
    ref: str  # Branch, tag, or commit SHA
    subpath: str  # Optional subdirectory path


def parse_github_url(url: str) -> GitHubURL:
    """Parse a github:// URL into components.

    Supports formats:
    - github://org/repo
    - github://org/repo@branch
    - github://org/repo@tag
    - github://org/repo@commit-sha
    - github://org/repo/subpath
    - github://org/repo@ref/subpath

    Args:
        url: GitHub URL string (e.g., "github://facebook/react@main")

    Returns:
        GitHubURL with parsed components

    Raises:
        ValueError: If URL format is invalid
    """
    if not url:
        raise ValueError("URL cannot be empty")

    # Pattern: github://org/repo[@ref][/subpath]
    pattern = r"^github://([^/]+)/([^/@]+)(?:@([^/]+))?(?:/(.*))?$"
    match = re.match(pattern, url)

    if not match:
        raise ValueError(
            f"Invalid GitHub URL format: {url}. "
            "Expected format: github://org/repo[@ref][/subpath]"
        )

    org, repo, ref, subpath = match.groups()

    # Validate org and repo are not empty after stripping whitespace
    if not org or not org.strip():
        raise ValueError("Organization name cannot be empty")
    if not repo or not repo.strip():
        raise ValueError("Repository name cannot be empty")

    # Default ref to "main" if not specified
    if not ref:
        ref = "main"

    # Normalize subpath (empty string if None)
    if not subpath:
        subpath = ""

    return GitHubURL(org=org, repo=repo, ref=ref, subpath=subpath)


def create_github_filesystem(url: str) -> GitHubFileSystem:
    """Create a GitHubFileSystem from a github:// URL.

    Validates that the repository is accessible and contains pareidolia.toml.

    Args:
        url: GitHub URL string

    Returns:
        Configured GitHubFileSystem instance

    Raises:
        ValueError: If URL format is invalid
        PareidoliaError: If repository is inaccessible or missing pareidolia.toml
    """
    # Parse URL
    parsed = parse_github_url(url)

    # Create GitHubFileSystem
    fs = GitHubFileSystem(
        org=parsed.org, repo=parsed.repo, ref=parsed.ref, subpath=parsed.subpath
    )

    # Validate pareidolia.toml exists
    if not fs.exists("pareidolia.toml"):
        raise PareidoliaError(
            f"Repository does not contain pareidolia.toml: {url}\n"
            f"Please check that the repository '{parsed.org}/{parsed.repo}' "
            f"exists and the ref '{parsed.ref}' is valid."
        )

    return fs
