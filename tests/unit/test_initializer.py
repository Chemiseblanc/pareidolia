"""Unit tests for ProjectInitializer class."""

import stat
import tomllib
from pathlib import Path

import pytest

from pareidolia.core.exceptions import ConfigurationError
from pareidolia.generators.initializer import ProjectInitializer


class TestCreateConfigFile:
    """Tests for ProjectInitializer.create_config_file method."""

    def test_create_config_file_creates_valid_toml(self, tmp_path: Path) -> None:
        """Test that config file is created with valid TOML syntax."""
        initializer = ProjectInitializer()
        initializer.create_config_file(tmp_path)

        config_path = tmp_path / "pareidolia.toml"
        assert config_path.exists(), "Config file should be created"

        # Verify file contains valid TOML by parsing it
        with open(config_path, "rb") as f:
            config_data = tomllib.load(f)

        # Verify expected sections exist
        assert "pareidolia" in config_data, "Should have [pareidolia] section"
        assert "generate" in config_data, "Should have [generate] section"

        # Verify expected default values
        assert config_data["pareidolia"]["root"] == "pareidolia"
        assert config_data["generate"]["tool"] == "standard"
        assert config_data["generate"]["output_dir"] == "prompts"

    def test_create_config_file_raises_error_if_exists_without_overwrite(
        self, tmp_path: Path
    ) -> None:
        """Test that existing file raises error when overwrite=False."""
        initializer = ProjectInitializer()
        config_path = tmp_path / "pareidolia.toml"

        # Create the file first
        config_path.write_text("# Existing config")

        # Attempt to create again without overwrite should raise error
        with pytest.raises(
            ConfigurationError,
            match="Configuration file already exists",
        ):
            initializer.create_config_file(tmp_path, overwrite=False)

        # Verify original content is unchanged
        assert config_path.read_text() == "# Existing config"

    def test_create_config_file_overwrites_with_flag(self, tmp_path: Path) -> None:
        """Test that file is overwritten when overwrite=True."""
        initializer = ProjectInitializer()
        config_path = tmp_path / "pareidolia.toml"

        # Create initial file
        config_path.write_text("# Old config")

        # Overwrite should succeed
        initializer.create_config_file(tmp_path, overwrite=True)

        # Verify new content replaced old content
        content = config_path.read_text()
        assert "# Old config" not in content
        assert "# Pareidolia Configuration File" in content

    def test_create_config_file_handles_permission_error(self, tmp_path: Path) -> None:
        """Test that permission errors are handled gracefully."""
        initializer = ProjectInitializer()

        # Make directory read-only to trigger permission error
        tmp_path.chmod(stat.S_IRUSR | stat.S_IXUSR)

        try:
            with pytest.raises(
                ConfigurationError,
                match="Permission denied.*configuration file",
            ):
                initializer.create_config_file(tmp_path)
        finally:
            # Restore permissions for cleanup
            tmp_path.chmod(stat.S_IRWXU)


class TestScaffoldDirectories:
    """Tests for ProjectInitializer.scaffold_directories method."""

    def test_scaffold_directories_creates_all_directories(
        self, tmp_path: Path
    ) -> None:
        """Test that all required directories are created."""
        initializer = ProjectInitializer()
        pareidolia_root = tmp_path / "project" / "pareidolia"

        initializer.scaffold_directories(pareidolia_root)

        # Check core directories under pareidolia root
        assert (pareidolia_root / "personas").is_dir()
        assert (pareidolia_root / "actions").is_dir()
        assert (pareidolia_root / "examples").is_dir()
        assert (pareidolia_root / "templates").is_dir()

        # Check output directory at project root level
        project_root = pareidolia_root.parent
        assert (project_root / "prompts").is_dir()

    def test_scaffold_directories_handles_existing_directories(
        self, tmp_path: Path
    ) -> None:
        """Test that existing directories don't cause errors (idempotent)."""
        initializer = ProjectInitializer()
        pareidolia_root = tmp_path / "project" / "pareidolia"

        # Create directories first
        (pareidolia_root / "personas").mkdir(parents=True)
        (pareidolia_root / "actions").mkdir(parents=True)

        # Should not raise error when directories exist
        initializer.scaffold_directories(pareidolia_root)

        # Should still have all directories
        assert (pareidolia_root / "personas").is_dir()
        assert (pareidolia_root / "actions").is_dir()
        assert (pareidolia_root / "examples").is_dir()
        assert (pareidolia_root / "templates").is_dir()

        # Can be called multiple times
        initializer.scaffold_directories(pareidolia_root)
        assert (pareidolia_root / "personas").is_dir()

    def test_scaffold_directories_handles_permission_error(
        self, tmp_path: Path
    ) -> None:
        """Test that permission errors are handled gracefully."""
        initializer = ProjectInitializer()
        pareidolia_root = tmp_path / "project" / "pareidolia"

        # Create parent directory but make it read-only
        pareidolia_root.parent.mkdir(parents=True)
        pareidolia_root.parent.chmod(stat.S_IRUSR | stat.S_IXUSR)

        try:
            with pytest.raises(
                ConfigurationError,
                match="Permission denied.*directory",
            ):
                initializer.scaffold_directories(pareidolia_root)
        finally:
            # Restore permissions for cleanup
            pareidolia_root.parent.chmod(stat.S_IRWXU)


class TestCreateExampleFiles:
    """Tests for ProjectInitializer.create_example_files method."""

    def test_create_example_files_creates_all_files(self, tmp_path: Path) -> None:
        """Test that all example files are created."""
        initializer = ProjectInitializer()
        pareidolia_root = tmp_path / "pareidolia"

        # Create directories first
        initializer.scaffold_directories(pareidolia_root)

        # Create example files
        initializer.create_example_files(pareidolia_root)

        # Verify all files exist and have content
        persona_file = pareidolia_root / "personas" / "researcher.md"
        assert persona_file.exists(), "Persona file should exist"
        assert len(persona_file.read_text()) > 0, "Persona file should have content"

        action_file = pareidolia_root / "actions" / "analyze.md.j2"
        assert action_file.exists(), "Action file should exist"
        assert len(action_file.read_text()) > 0, "Action file should have content"

        example_file = pareidolia_root / "examples" / "analysis-output.md"
        assert example_file.exists(), "Example file should exist"
        assert len(example_file.read_text()) > 0, "Example file should have content"

        readme_file = pareidolia_root / "templates" / "README.md"
        assert readme_file.exists(), "Templates README should exist"
        assert len(readme_file.read_text()) > 0, "Templates README should have content"

    def test_create_example_files_content_is_valid(self, tmp_path: Path) -> None:
        """Test that example file content is valid and useful."""
        initializer = ProjectInitializer()
        pareidolia_root = tmp_path / "pareidolia"

        # Create directories and files
        initializer.scaffold_directories(pareidolia_root)
        initializer.create_example_files(pareidolia_root)

        # Verify persona content
        persona_content = (pareidolia_root / "personas" / "researcher.md").read_text()
        assert "# Researcher Persona" in persona_content
        assert len(persona_content) > 50, "Persona should have substantive content"

        # Verify action is valid Jinja2 template
        action_content = (pareidolia_root / "actions" / "analyze.md.j2").read_text()
        assert "{{" in action_content, "Action should contain Jinja2 variables"
        assert "{%" in action_content, "Action should contain Jinja2 logic"
        assert "persona" in action_content, "Action should reference persona"

        # Verify example has valid markdown
        example_content = (
            pareidolia_root / "examples" / "analysis-output.md"
        ).read_text()
        assert example_content.startswith("#"), "Example should be markdown"
        assert "##" in example_content, "Example should have sections"

        # Verify templates README is helpful
        readme_content = (pareidolia_root / "templates" / "README.md").read_text()
        assert "# Custom Templates" in readme_content
        assert "include" in readme_content, "README should explain template usage"
        assert "Example" in readme_content, "README should have examples"

    def test_create_example_files_handles_permission_error(
        self, tmp_path: Path
    ) -> None:
        """Test that permission errors are handled gracefully."""
        initializer = ProjectInitializer()
        pareidolia_root = tmp_path / "pareidolia"

        # Create directories
        initializer.scaffold_directories(pareidolia_root)

        # Make personas directory read-only
        personas_dir = pareidolia_root / "personas"
        personas_dir.chmod(stat.S_IRUSR | stat.S_IXUSR)

        try:
            with pytest.raises(
                ConfigurationError,
                match="Permission denied.*example file",
            ):
                initializer.create_example_files(pareidolia_root)
        finally:
            # Restore permissions for cleanup
            personas_dir.chmod(stat.S_IRWXU)


class TestCreateGitignore:
    """Tests for ProjectInitializer.create_gitignore method."""

    def test_create_gitignore_creates_file(self, tmp_path: Path) -> None:
        """Test that .gitignore file is created with correct content."""
        initializer = ProjectInitializer()
        output_dir = tmp_path / "prompts"
        output_dir.mkdir()

        initializer.create_gitignore(output_dir)

        gitignore_path = output_dir / ".gitignore"
        assert gitignore_path.exists(), ".gitignore should be created"

        content = gitignore_path.read_text()
        assert "*" in content, "Should ignore all files"
        assert "!.gitignore" in content, "Should keep .gitignore itself"

    def test_create_gitignore_handles_permission_error(self, tmp_path: Path) -> None:
        """Test that permission errors are handled gracefully."""
        initializer = ProjectInitializer()
        output_dir = tmp_path / "prompts"
        output_dir.mkdir()

        # Make directory read-only
        output_dir.chmod(stat.S_IRUSR | stat.S_IXUSR)

        try:
            with pytest.raises(
                ConfigurationError,
                match="Permission denied.*\\.gitignore",
            ):
                initializer.create_gitignore(output_dir)
        finally:
            # Restore permissions for cleanup
            output_dir.chmod(stat.S_IRWXU)


class TestFullInitializationWorkflow:
    """Integration-style tests for complete initialization workflow."""

    def test_full_initialization_workflow(self, tmp_path: Path) -> None:
        """Test complete project initialization workflow."""
        initializer = ProjectInitializer()
        project_root = tmp_path / "my-project"
        pareidolia_root = project_root / "pareidolia"
        prompts_dir = project_root / "prompts"

        # Create project root directory
        project_root.mkdir(parents=True)

        # Step 1: Create config file
        initializer.create_config_file(project_root)
        assert (project_root / "pareidolia.toml").exists()

        # Step 2: Scaffold directories
        initializer.scaffold_directories(pareidolia_root)
        assert (pareidolia_root / "personas").is_dir()
        assert (pareidolia_root / "actions").is_dir()
        assert (pareidolia_root / "examples").is_dir()
        assert (pareidolia_root / "templates").is_dir()
        assert prompts_dir.is_dir()

        # Step 3: Create example files
        initializer.create_example_files(pareidolia_root)
        assert (pareidolia_root / "personas" / "researcher.md").exists()
        assert (pareidolia_root / "actions" / "analyze.md.j2").exists()
        assert (pareidolia_root / "examples" / "analysis-output.md").exists()
        assert (pareidolia_root / "templates" / "README.md").exists()

        # Step 4: Create gitignore
        initializer.create_gitignore(prompts_dir)
        assert (prompts_dir / ".gitignore").exists()

        # Verify config is valid and parseable
        with open(project_root / "pareidolia.toml", "rb") as f:
            config_data = tomllib.load(f)

        assert config_data["pareidolia"]["root"] == "pareidolia"
        assert config_data["generate"]["output_dir"] == "prompts"

        # Verify all expected files exist
        expected_files = [
            project_root / "pareidolia.toml",
            pareidolia_root / "personas" / "researcher.md",
            pareidolia_root / "actions" / "analyze.md.j2",
            pareidolia_root / "examples" / "analysis-output.md",
            pareidolia_root / "templates" / "README.md",
            prompts_dir / ".gitignore",
        ]

        for file_path in expected_files:
            assert file_path.exists(), f"{file_path} should exist"
            assert file_path.stat().st_size > 0, f"{file_path} should have content"

    def test_initialization_with_custom_paths(self, tmp_path: Path) -> None:
        """Test initialization with custom directory structure."""
        initializer = ProjectInitializer()
        project_root = tmp_path / "custom-project"
        custom_root = project_root / "custom-dir"

        # Create project root directory
        project_root.mkdir(parents=True)

        # Initialize with custom paths
        initializer.create_config_file(project_root)
        initializer.scaffold_directories(custom_root)
        initializer.create_example_files(custom_root)

        # Verify structure
        assert (custom_root / "personas").is_dir()
        assert (custom_root / "actions").is_dir()
        assert (custom_root / "examples").is_dir()
        assert (custom_root / "templates").is_dir()
        assert (project_root / "prompts").is_dir()

    def test_initialization_is_idempotent(self, tmp_path: Path) -> None:
        """Test that initialization can be run multiple times safely."""
        initializer = ProjectInitializer()
        project_root = tmp_path / "project"
        pareidolia_root = project_root / "pareidolia"

        # Create project root directory
        project_root.mkdir(parents=True)

        # Run full initialization
        initializer.create_config_file(project_root)
        initializer.scaffold_directories(pareidolia_root)
        initializer.create_example_files(pareidolia_root)

        # Get file modification times
        config_mtime = (project_root / "pareidolia.toml").stat().st_mtime

        # Run scaffold again (should be safe)
        initializer.scaffold_directories(pareidolia_root)

        # Directories should still exist
        assert (pareidolia_root / "personas").is_dir()

        # Config file should be unchanged (we didn't call create_config_file
        # with overwrite)
        assert (project_root / "pareidolia.toml").stat().st_mtime == config_mtime

        # Note: create_example_files is NOT idempotent by design - it will
        # overwrite files. We only test that scaffold_directories is idempotent.
