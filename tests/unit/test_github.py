"""Unit tests for GitHub URL parsing and filesystem."""

from unittest.mock import MagicMock, Mock, patch
from urllib.error import HTTPError, URLError

import pytest

from pareidolia.core.exceptions import PareidoliaError
from pareidolia.utils.filesystem import GitHubFileSystem
from pareidolia.utils.github import (
    GitHubURL,
    create_github_filesystem,
    parse_github_url,
)


class TestParseGitHubURL:
    """Tests for GitHub URL parsing."""

    def test_parse_github_url_basic(self) -> None:
        """Test parsing basic github:// URL."""
        result = parse_github_url("github://facebook/react")
        assert result.org == "facebook"
        assert result.repo == "react"
        assert result.ref == "main"  # Default
        assert result.subpath == ""

    def test_parse_github_url_with_branch(self) -> None:
        """Test parsing URL with explicit branch."""
        result = parse_github_url("github://microsoft/vscode@develop")
        assert result.org == "microsoft"
        assert result.repo == "vscode"
        assert result.ref == "develop"
        assert result.subpath == ""

    def test_parse_github_url_with_tag(self) -> None:
        """Test parsing URL with tag reference."""
        result = parse_github_url("github://torvalds/linux@v6.5")
        assert result.org == "torvalds"
        assert result.repo == "linux"
        assert result.ref == "v6.5"
        assert result.subpath == ""

    def test_parse_github_url_with_commit_sha(self) -> None:
        """Test parsing URL with commit SHA."""
        result = parse_github_url("github://rails/rails@abc123def456")
        assert result.org == "rails"
        assert result.repo == "rails"
        assert result.ref == "abc123def456"
        assert result.subpath == ""

    def test_parse_github_url_with_subpath(self) -> None:
        """Test parsing URL with subdirectory path."""
        result = parse_github_url("github://org/repo/prompts/personas")
        assert result.org == "org"
        assert result.repo == "repo"
        assert result.ref == "main"
        assert result.subpath == "prompts/personas"

    def test_parse_github_url_with_branch_and_subpath(self) -> None:
        """Test parsing URL with both branch and subpath."""
        result = parse_github_url("github://org/repo@develop/src/templates")
        assert result.org == "org"
        assert result.repo == "repo"
        assert result.ref == "develop"
        assert result.subpath == "src/templates"

    def test_parse_github_url_with_deep_subpath(self) -> None:
        """Test parsing URL with deep subdirectory path."""
        result = parse_github_url("github://org/repo/a/b/c/d/e")
        assert result.org == "org"
        assert result.repo == "repo"
        assert result.ref == "main"
        assert result.subpath == "a/b/c/d/e"

    def test_parse_github_url_invalid_scheme(self) -> None:
        """Test that non-github:// URLs are rejected."""
        with pytest.raises(ValueError, match="Invalid GitHub URL"):
            parse_github_url("https://github.com/org/repo")

        with pytest.raises(ValueError, match="Invalid GitHub URL"):
            parse_github_url("http://github.com/org/repo")

        with pytest.raises(ValueError, match="Invalid GitHub URL"):
            parse_github_url("git@github.com:org/repo.git")

    def test_parse_github_url_missing_repo(self) -> None:
        """Test that URLs without repo name are rejected."""
        with pytest.raises(ValueError, match="Invalid GitHub URL"):
            parse_github_url("github://org")

        with pytest.raises(ValueError, match="Invalid GitHub URL"):
            parse_github_url("github://org/")

    def test_parse_github_url_empty_org(self) -> None:
        """Test that empty organization name is rejected."""
        with pytest.raises(ValueError, match="Invalid GitHub URL"):
            parse_github_url("github:///repo")

    def test_parse_github_url_empty_repo(self) -> None:
        """Test that empty repository name is rejected."""
        with pytest.raises(ValueError, match="Invalid GitHub URL"):
            parse_github_url("github://org//subpath")

    def test_parse_github_url_empty_string(self) -> None:
        """Test that empty URL is rejected."""
        with pytest.raises(ValueError, match="URL cannot be empty"):
            parse_github_url("")

    def test_parse_github_url_whitespace_org(self) -> None:
        """Test that whitespace-only org name is rejected."""
        with pytest.raises(ValueError, match="Organization name cannot be empty"):
            parse_github_url("github://   /repo")

    def test_parse_github_url_whitespace_repo(self) -> None:
        """Test that whitespace-only repo name is rejected."""
        with pytest.raises(ValueError, match="Repository name cannot be empty"):
            parse_github_url("github://org/   ")

    def test_parse_github_url_special_characters_in_org(self) -> None:
        """Test URLs with special characters in org name."""
        result = parse_github_url("github://org-name_123/repo")
        assert result.org == "org-name_123"
        assert result.repo == "repo"

    def test_parse_github_url_special_characters_in_repo(self) -> None:
        """Test URLs with special characters in repo name."""
        result = parse_github_url("github://org/repo.name-test_2")
        assert result.org == "org"
        assert result.repo == "repo.name-test_2"

    def test_parse_github_url_ref_with_special_chars(self) -> None:
        """Test refs with special characters."""
        result = parse_github_url("github://org/repo@feature-user-auth_v2.1")
        assert result.org == "org"
        assert result.repo == "repo"
        assert result.ref == "feature-user-auth_v2.1"

    def test_parse_github_url_returns_namedtuple(self) -> None:
        """Test that result is a proper NamedTuple."""
        result = parse_github_url("github://org/repo@main/path")
        assert isinstance(result, GitHubURL)
        assert isinstance(result, tuple)
        # Test named access
        assert result.org == "org"
        # Test indexed access
        assert result[0] == "org"

    def test_parse_github_url_subpath_normalization(self) -> None:
        """Test that subpath without ref is handled correctly."""
        result = parse_github_url("github://org/repo/templates")
        assert result.ref == "main"
        assert result.subpath == "templates"


class TestCreateGitHubFileSystem:
    """Tests for GitHub filesystem creation."""

    @patch("pareidolia.utils.github.GitHubFileSystem")
    def test_create_github_filesystem_success(self, mock_fs_class: Mock) -> None:
        """Test successful filesystem creation."""
        # Setup mock
        mock_fs = Mock(spec=GitHubFileSystem)
        mock_fs.exists.return_value = True
        mock_fs_class.return_value = mock_fs

        # Call function
        result = create_github_filesystem("github://org/repo")

        # Verify
        assert result == mock_fs
        mock_fs_class.assert_called_once_with(
            org="org", repo="repo", ref="main", subpath=""
        )
        mock_fs.exists.assert_called_once_with("pareidolia.toml")

    @patch("pareidolia.utils.github.GitHubFileSystem")
    def test_create_github_filesystem_with_branch(self, mock_fs_class: Mock) -> None:
        """Test filesystem creation with specific branch."""
        mock_fs = Mock(spec=GitHubFileSystem)
        mock_fs.exists.return_value = True
        mock_fs_class.return_value = mock_fs

        result = create_github_filesystem("github://org/repo@develop")

        assert result == mock_fs
        mock_fs_class.assert_called_once_with(
            org="org", repo="repo", ref="develop", subpath=""
        )

    @patch("pareidolia.utils.github.GitHubFileSystem")
    def test_create_github_filesystem_with_subpath(self, mock_fs_class: Mock) -> None:
        """Test filesystem creation with subpath."""
        mock_fs = Mock(spec=GitHubFileSystem)
        mock_fs.exists.return_value = True
        mock_fs_class.return_value = mock_fs

        result = create_github_filesystem("github://org/repo/prompts")

        assert result == mock_fs
        mock_fs_class.assert_called_once_with(
            org="org", repo="repo", ref="main", subpath="prompts"
        )

    @patch("pareidolia.utils.github.GitHubFileSystem")
    def test_create_github_filesystem_no_config(self, mock_fs_class: Mock) -> None:
        """Test error when pareidolia.toml not found."""
        # Setup mock to return False for exists
        mock_fs = Mock(spec=GitHubFileSystem)
        mock_fs.exists.return_value = False
        mock_fs_class.return_value = mock_fs

        # Should raise PareidoliaError
        with pytest.raises(
            PareidoliaError, match="Repository does not contain pareidolia.toml"
        ):
            create_github_filesystem("github://org/repo")

    @patch("pareidolia.utils.github.GitHubFileSystem")
    def test_create_github_filesystem_no_config_includes_url(
        self, mock_fs_class: Mock
    ) -> None:
        """Test error message includes the URL."""
        mock_fs = Mock(spec=GitHubFileSystem)
        mock_fs.exists.return_value = False
        mock_fs_class.return_value = mock_fs

        with pytest.raises(PareidoliaError, match="github://org/repo@main"):
            create_github_filesystem("github://org/repo@main")

    @patch("pareidolia.utils.github.GitHubFileSystem")
    def test_create_github_filesystem_no_config_includes_ref(
        self, mock_fs_class: Mock
    ) -> None:
        """Test error message includes ref information."""
        mock_fs = Mock(spec=GitHubFileSystem)
        mock_fs.exists.return_value = False
        mock_fs_class.return_value = mock_fs

        with pytest.raises(PareidoliaError, match="ref 'v1.0.0' is valid"):
            create_github_filesystem("github://org/repo@v1.0.0")

    def test_create_github_filesystem_invalid_url(self) -> None:
        """Test that invalid URLs are rejected."""
        with pytest.raises(ValueError, match="Invalid GitHub URL"):
            create_github_filesystem("https://github.com/org/repo")

    @patch("pareidolia.utils.github.GitHubFileSystem")
    def test_create_github_filesystem_network_error(
        self, mock_fs_class: Mock
    ) -> None:
        """Test handling of network errors during validation."""
        # Setup mock to raise error on exists check
        mock_fs = Mock(spec=GitHubFileSystem)
        mock_fs.exists.side_effect = OSError("Network error")
        mock_fs_class.return_value = mock_fs

        # Should propagate the OSError
        with pytest.raises(OSError, match="Network error"):
            create_github_filesystem("github://org/repo")


class TestGitHubFileSystem:
    """Tests for GitHubFileSystem operations."""

    @patch("urllib.request.urlopen")
    def test_read_file_success(self, mock_urlopen: Mock) -> None:
        """Test successful file reading from GitHub."""
        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.read.return_value = b"file content"
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        fs = GitHubFileSystem("org", "repo", "main", "")
        content = fs.read_file("personas/researcher.md")

        assert content == "file content"
        # Verify URL construction
        expected_url = (
            "https://raw.githubusercontent.com/org/repo/main/personas/researcher.md"
        )
        mock_urlopen.assert_called_once()
        args = mock_urlopen.call_args[0]
        assert args[0] == expected_url

    @patch("urllib.request.urlopen")
    def test_read_file_with_subpath(self, mock_urlopen: Mock) -> None:
        """Test file reading with subpath in filesystem."""
        mock_response = MagicMock()
        mock_response.read.return_value = b"content"
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        fs = GitHubFileSystem("org", "repo", "main", "prompts")
        content = fs.read_file("researcher.md")

        assert content == "content"
        expected_url = (
            "https://raw.githubusercontent.com/org/repo/main/prompts/researcher.md"
        )
        args = mock_urlopen.call_args[0]
        assert args[0] == expected_url

    @patch("urllib.request.urlopen")
    def test_read_file_with_branch(self, mock_urlopen: Mock) -> None:
        """Test file reading from specific branch."""
        mock_response = MagicMock()
        mock_response.read.return_value = b"branch content"
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        fs = GitHubFileSystem("org", "repo", "develop", "")
        content = fs.read_file("test.md")

        assert content == "branch content"
        expected_url = "https://raw.githubusercontent.com/org/repo/develop/test.md"
        args = mock_urlopen.call_args[0]
        assert args[0] == expected_url

    @patch("urllib.request.urlopen")
    def test_read_file_404(self, mock_urlopen: Mock) -> None:
        """Test file not found error."""
        # Mock 404 error
        mock_urlopen.side_effect = HTTPError("url", 404, "Not Found", {}, None)

        fs = GitHubFileSystem("org", "repo", "main", "")

        with pytest.raises(FileNotFoundError, match="File not found on GitHub"):
            fs.read_file("missing.md")

    @patch("urllib.request.urlopen")
    def test_read_file_404_includes_path(self, mock_urlopen: Mock) -> None:
        """Test that 404 error message includes the GitHub path."""
        mock_urlopen.side_effect = HTTPError("url", 404, "Not Found", {}, None)

        fs = GitHubFileSystem("myorg", "myrepo", "mybranch", "")

        with pytest.raises(
            FileNotFoundError, match="myorg/myrepo/mybranch/test.md"
        ):
            fs.read_file("test.md")

    @patch("urllib.request.urlopen")
    def test_read_file_http_error_500(self, mock_urlopen: Mock) -> None:
        """Test handling of server errors."""
        mock_urlopen.side_effect = HTTPError(
            "url", 500, "Internal Server Error", {}, None
        )

        fs = GitHubFileSystem("org", "repo", "main", "")

        with pytest.raises(OSError, match="Failed to fetch file from GitHub"):
            fs.read_file("test.md")

    @patch("urllib.request.urlopen")
    def test_read_file_http_error_403(self, mock_urlopen: Mock) -> None:
        """Test handling of forbidden errors."""
        mock_urlopen.side_effect = HTTPError("url", 403, "Forbidden", {}, None)

        fs = GitHubFileSystem("org", "repo", "main", "")

        with pytest.raises(OSError, match="HTTP 403"):
            fs.read_file("test.md")

    @patch("urllib.request.urlopen")
    def test_read_file_network_error(self, mock_urlopen: Mock) -> None:
        """Test handling of network errors."""
        mock_urlopen.side_effect = URLError("Network unreachable")

        fs = GitHubFileSystem("org", "repo", "main", "")

        with pytest.raises(OSError, match="Network error fetching file from GitHub"):
            fs.read_file("test.md")

    @patch("urllib.request.urlopen")
    def test_read_file_timeout(self, mock_urlopen: Mock) -> None:
        """Test handling of timeout errors."""

        mock_urlopen.side_effect = TimeoutError("Request timed out")

        fs = GitHubFileSystem("org", "repo", "main", "")

        with pytest.raises(OSError, match="Error reading file from GitHub"):
            fs.read_file("test.md")

    @patch("urllib.request.urlopen")
    def test_read_file_caching(self, mock_urlopen: Mock) -> None:
        """Test that files are cached after first read."""
        mock_response = MagicMock()
        mock_response.read.return_value = b"cached content"
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        fs = GitHubFileSystem("org", "repo", "main", "")

        # First read
        content1 = fs.read_file("test.md")
        # Second read (should use cache)
        content2 = fs.read_file("test.md")

        assert content1 == content2 == "cached content"
        # urlopen should only be called once
        assert mock_urlopen.call_count == 1

    @patch("urllib.request.urlopen")
    def test_read_file_cache_different_files(self, mock_urlopen: Mock) -> None:
        """Test that cache is per-file."""
        mock_response1 = MagicMock()
        mock_response1.read.return_value = b"content1"
        mock_response1.__enter__.return_value = mock_response1

        mock_response2 = MagicMock()
        mock_response2.read.return_value = b"content2"
        mock_response2.__enter__.return_value = mock_response2

        mock_urlopen.side_effect = [mock_response1, mock_response2]

        fs = GitHubFileSystem("org", "repo", "main", "")

        # Read two different files
        content1 = fs.read_file("file1.md")
        content2 = fs.read_file("file2.md")

        assert content1 == "content1"
        assert content2 == "content2"
        assert mock_urlopen.call_count == 2

    @patch("urllib.request.urlopen")
    def test_read_file_utf8_decoding(self, mock_urlopen: Mock) -> None:
        """Test UTF-8 decoding of file content."""
        # Use actual UTF-8 encoded content
        utf8_content = "Hello 世界! 🌍".encode()
        mock_response = MagicMock()
        mock_response.read.return_value = utf8_content
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        fs = GitHubFileSystem("org", "repo", "main", "")
        content = fs.read_file("test.md")

        assert content == "Hello 世界! 🌍"

    @patch("urllib.request.urlopen")
    def test_read_file_leading_slash_stripped(self, mock_urlopen: Mock) -> None:
        """Test that leading slashes in paths are stripped."""
        mock_response = MagicMock()
        mock_response.read.return_value = b"content"
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        fs = GitHubFileSystem("org", "repo", "main", "")
        content = fs.read_file("/test.md")

        assert content == "content"
        # Verify URL doesn't have double slash
        expected_url = "https://raw.githubusercontent.com/org/repo/main/test.md"
        args = mock_urlopen.call_args[0]
        assert args[0] == expected_url

    @patch("urllib.request.urlopen")
    def test_read_file_timeout_parameter(self, mock_urlopen: Mock) -> None:
        """Test that timeout is passed to urlopen."""
        from pareidolia.utils.filesystem import GITHUB_REQUEST_TIMEOUT

        mock_response = MagicMock()
        mock_response.read.return_value = b"content"
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        fs = GitHubFileSystem("org", "repo", "main", "")
        fs.read_file("test.md")

        # Verify timeout parameter
        kwargs = mock_urlopen.call_args[1]
        assert kwargs["timeout"] == GITHUB_REQUEST_TIMEOUT

    @patch("urllib.request.urlopen")
    def test_exists_returns_true_when_file_exists(self, mock_urlopen: Mock) -> None:
        """Test exists returns True for existing files."""
        mock_response = MagicMock()
        mock_response.read.return_value = b"content"
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        fs = GitHubFileSystem("org", "repo", "main", "")
        assert fs.exists("test.md") is True

    @patch("urllib.request.urlopen")
    def test_exists_returns_false_on_404(self, mock_urlopen: Mock) -> None:
        """Test exists returns False when file not found."""
        mock_urlopen.side_effect = HTTPError("url", 404, "Not Found", {}, None)

        fs = GitHubFileSystem("org", "repo", "main", "")
        assert fs.exists("missing.md") is False

    @patch("urllib.request.urlopen")
    def test_exists_returns_false_on_network_error(self, mock_urlopen: Mock) -> None:
        """Test exists returns False on network errors."""
        mock_urlopen.side_effect = URLError("Network error")

        fs = GitHubFileSystem("org", "repo", "main", "")
        assert fs.exists("test.md") is False

    @patch("urllib.request.urlopen")
    def test_exists_uses_cache(self, mock_urlopen: Mock) -> None:
        """Test that exists uses cached content."""
        mock_response = MagicMock()
        mock_response.read.return_value = b"content"
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        fs = GitHubFileSystem("org", "repo", "main", "")

        # First read to populate cache
        fs.read_file("test.md")
        # exists should use cache
        assert fs.exists("test.md") is True

        # Should only call urlopen once (for read_file)
        assert mock_urlopen.call_count == 1

    def test_is_readonly(self) -> None:
        """Test that GitHub filesystem is read-only."""
        fs = GitHubFileSystem("org", "repo", "main", "")
        assert fs.is_readonly() is True

    def test_list_files_returns_empty(self) -> None:
        """Test that list_files returns empty (not supported)."""
        fs = GitHubFileSystem("org", "repo", "main", "")
        result = fs.list_files("personas", "*.md")
        assert result == []

    def test_list_files_always_empty_regardless_of_args(self) -> None:
        """Test that list_files always returns empty list."""
        fs = GitHubFileSystem("org", "repo", "main", "")
        assert fs.list_files("", "") == []
        assert fs.list_files("any/path", "**/*") == []
        assert fs.list_files(".", "*") == []

    def test_build_url_basic(self) -> None:
        """Test URL construction for basic case."""
        fs = GitHubFileSystem("org", "repo", "main", "")
        url = fs._build_url("test.md")
        assert url == "https://raw.githubusercontent.com/org/repo/main/test.md"

    def test_build_url_with_subpath(self) -> None:
        """Test URL construction with subpath."""
        fs = GitHubFileSystem("org", "repo", "main", "prompts")
        url = fs._build_url("test.md")
        assert (
            url == "https://raw.githubusercontent.com/org/repo/main/prompts/test.md"
        )

    def test_build_url_with_branch(self) -> None:
        """Test URL construction with non-main branch."""
        fs = GitHubFileSystem("org", "repo", "develop", "")
        url = fs._build_url("test.md")
        assert url == "https://raw.githubusercontent.com/org/repo/develop/test.md"

    def test_build_url_with_nested_path(self) -> None:
        """Test URL construction with nested file path."""
        fs = GitHubFileSystem("org", "repo", "main", "")
        url = fs._build_url("a/b/c/test.md")
        assert url == "https://raw.githubusercontent.com/org/repo/main/a/b/c/test.md"

    def test_build_url_strips_leading_slash(self) -> None:
        """Test that leading slashes are stripped from paths."""
        fs = GitHubFileSystem("org", "repo", "main", "")
        url = fs._build_url("/test.md")
        assert url == "https://raw.githubusercontent.com/org/repo/main/test.md"

    def test_init_normalizes_subpath_trailing_slash(self) -> None:
        """Test that trailing slashes are removed from subpath."""
        fs = GitHubFileSystem("org", "repo", "main", "prompts/")
        assert fs.subpath == "prompts"

        fs2 = GitHubFileSystem("org", "repo", "main", "a/b/c/")
        assert fs2.subpath == "a/b/c"

    def test_init_empty_subpath(self) -> None:
        """Test initialization with empty subpath."""
        fs = GitHubFileSystem("org", "repo", "main", "")
        assert fs.subpath == ""

    def test_cache_isolation_between_instances(self) -> None:
        """Test that cache is per-instance, not shared."""
        fs1 = GitHubFileSystem("org1", "repo1", "main", "")
        fs2 = GitHubFileSystem("org2", "repo2", "main", "")

        # Different instances should have different caches
        assert fs1._cache is not fs2._cache

        # Modifying one cache shouldn't affect the other
        fs1._cache["test.md"] = "content1"
        fs2._cache["test.md"] = "content2"

        assert fs1._cache["test.md"] == "content1"
        assert fs2._cache["test.md"] == "content2"

    def test_attributes_stored_correctly(self) -> None:
        """Test that initialization stores all attributes."""
        fs = GitHubFileSystem("myorg", "myrepo", "mybranch", "mypath")
        assert fs.org == "myorg"
        assert fs.repo == "myrepo"
        assert fs.ref == "mybranch"
        assert fs.subpath == "mypath"

    def test_default_ref_parameter(self) -> None:
        """Test that ref defaults to 'main' if not provided."""
        fs = GitHubFileSystem("org", "repo")
        assert fs.ref == "main"
