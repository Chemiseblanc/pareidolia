"""Integration tests for the init command."""

import subprocess
import sys
from pathlib import Path

import pytest

from pareidolia.core.config import PareidoliaConfig


def run_init_command(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    """Run the pareidolia init command with given arguments.

    Args:
        args: Command line arguments (e.g., ['init', 'my-project'])
        cwd: Working directory to run command in

    Returns:
        CompletedProcess with stdout, stderr, and return code
    """
    cmd = [sys.executable, "-m", "pareidolia"] + args
    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
    )


def test_init_in_current_directory(tmp_path: Path) -> None:
    """Test init command in current directory with default scaffolding."""
    # Run init in temp directory
    result = run_init_command(["init"], cwd=tmp_path)

    # Verify success
    assert result.returncode == 0, f"Command failed: {result.stderr}"
    assert "Project initialized successfully!" in result.stdout

    # Verify config file created
    config_file = tmp_path / ".pareidolia.toml"
    assert config_file.exists()

    # Verify directory structure created
    pareidolia_dir = tmp_path / "pareidolia"
    assert pareidolia_dir.exists()
    assert pareidolia_dir.is_dir()

    # Verify subdirectories
    assert (pareidolia_dir / "personas").exists()
    assert (pareidolia_dir / "actions").exists()
    assert (pareidolia_dir / "examples").exists()
    assert (pareidolia_dir / "templates").exists()

    # Verify prompts directory
    prompts_dir = tmp_path / "prompts"
    assert prompts_dir.exists()
    assert prompts_dir.is_dir()

    # Verify example files exist
    assert (pareidolia_dir / "personas" / "researcher.md").exists()
    assert (pareidolia_dir / "actions" / "analyze.md.j2").exists()
    assert (pareidolia_dir / "examples" / "analysis-output.md").exists()
    assert (pareidolia_dir / "templates" / "README.md").exists()

    # Verify .gitignore in prompts directory
    gitignore = prompts_dir / ".gitignore"
    assert gitignore.exists()
    gitignore_content = gitignore.read_text()
    assert "*" in gitignore_content
    assert "!.gitignore" in gitignore_content

    # Verify success messages
    assert "Created configuration file" in result.stdout
    assert "Created directory structure" in result.stdout
    assert "Created example files" in result.stdout


def test_init_in_specific_directory(tmp_path: Path) -> None:
    """Test init command with specific directory argument."""
    project_name = "my-project"

    # Run init with directory name
    result = run_init_command(["init", project_name], cwd=tmp_path)

    # Verify success
    assert result.returncode == 0, f"Command failed: {result.stderr}"
    assert "Project initialized successfully!" in result.stdout

    # Verify project directory created
    project_dir = tmp_path / project_name
    assert project_dir.exists()
    assert project_dir.is_dir()

    # Verify structure is created in the specified directory
    config_file = project_dir / ".pareidolia.toml"
    assert config_file.exists()

    pareidolia_dir = project_dir / "pareidolia"
    assert pareidolia_dir.exists()

    # Verify subdirectories
    assert (pareidolia_dir / "personas").exists()
    assert (pareidolia_dir / "actions").exists()
    assert (pareidolia_dir / "examples").exists()
    assert (pareidolia_dir / "templates").exists()

    # Verify prompts directory
    prompts_dir = project_dir / "prompts"
    assert prompts_dir.exists()

    # Verify example files
    assert (pareidolia_dir / "personas" / "researcher.md").exists()
    assert (pareidolia_dir / "actions" / "analyze.md.j2").exists()


def test_init_with_no_scaffold_flag(tmp_path: Path) -> None:
    """Test init command with --no-scaffold flag."""
    # Run init with --no-scaffold
    result = run_init_command(["init", "--no-scaffold"], cwd=tmp_path)

    # Verify success
    assert result.returncode == 0, f"Command failed: {result.stderr}"
    assert "Project initialized successfully!" in result.stdout

    # Verify config file created
    config_file = tmp_path / ".pareidolia.toml"
    assert config_file.exists()

    # Verify config created message but not scaffolding messages
    assert "Created configuration file" in result.stdout
    assert "Created directory structure" not in result.stdout
    assert "Created example files" not in result.stdout

    # Verify directory structure NOT created
    pareidolia_dir = tmp_path / "pareidolia"
    assert not pareidolia_dir.exists()

    # Verify prompts directory NOT created
    prompts_dir = tmp_path / "prompts"
    assert not prompts_dir.exists()

    # Verify no example files created
    assert not (tmp_path / "personas").exists()
    assert not (tmp_path / "actions").exists()
    assert not (tmp_path / "examples").exists()
    assert not (tmp_path / "templates").exists()


def test_init_specific_dir_with_no_scaffold(tmp_path: Path) -> None:
    """Test init command with specific directory and --no-scaffold."""
    project_name = "my-project"

    # Run init with directory and --no-scaffold
    result = run_init_command(
        ["init", project_name, "--no-scaffold"],
        cwd=tmp_path,
    )

    # Verify success
    assert result.returncode == 0, f"Command failed: {result.stderr}"

    # Verify project directory created
    project_dir = tmp_path / project_name
    assert project_dir.exists()

    # Verify only config file exists
    config_file = project_dir / ".pareidolia.toml"
    assert config_file.exists()

    # Verify no scaffolding
    pareidolia_dir = project_dir / "pareidolia"
    assert not pareidolia_dir.exists()

    prompts_dir = project_dir / "prompts"
    assert not prompts_dir.exists()


def test_init_with_existing_config_file(tmp_path: Path) -> None:
    """Test init command fails when config file already exists."""
    # Create existing config file
    config_file = tmp_path / ".pareidolia.toml"
    config_file.write_text("[pareidolia]\nroot = 'test'\n")

    # Run init
    result = run_init_command(["init"], cwd=tmp_path)

    # Verify failure
    assert result.returncode == 1, "Expected command to fail"

    # Verify error message
    assert "already exists" in result.stderr or "already exists" in result.stdout


def test_init_help(tmp_path: Path) -> None:
    """Test init command help output."""
    # Run init --help
    result = run_init_command(["init", "--help"], cwd=tmp_path)

    # Verify success
    assert result.returncode == 0

    # Verify help content
    help_text = result.stdout

    # Check for command description
    assert "init" in help_text.lower()
    assert "initialize" in help_text.lower() or "Initialize" in help_text

    # Check for directory argument
    assert "directory" in help_text

    # Check for --no-scaffold option
    assert "--no-scaffold" in help_text

    # Verify description explains what the flag does
    assert (
        "configuration" in help_text.lower()
        or "config" in help_text.lower()
    )


def test_init_creates_valid_parseable_config(tmp_path: Path) -> None:
    """Test that init creates a valid, parseable configuration file."""
    # Run init
    result = run_init_command(["init"], cwd=tmp_path)
    assert result.returncode == 0

    # Load the created config file
    config_file = tmp_path / ".pareidolia.toml"
    assert config_file.exists()

    # Parse the config file using PareidoliaConfig
    config = PareidoliaConfig.from_file(config_file)

    # Verify config loaded successfully (no exceptions raised)
    assert config is not None

    # Verify expected default values
    assert config.root == tmp_path / "pareidolia"
    assert config.export.tool == "standard"
    assert config.export.output_dir == tmp_path / "prompts"

    # Verify structure
    assert hasattr(config, "export")
    assert hasattr(config, "variants")


def test_init_config_file_content(tmp_path: Path) -> None:
    """Test that init creates config file with proper content and comments."""
    # Run init
    result = run_init_command(["init"], cwd=tmp_path)
    assert result.returncode == 0

    # Read the config file content
    config_file = tmp_path / ".pareidolia.toml"
    content = config_file.read_text()

    # Verify it's valid TOML format
    assert "[pareidolia]" in content
    assert "[export]" in content

    # Verify required fields are present
    assert "root" in content
    assert "tool" in content
    assert "output_dir" in content

    # Verify it contains helpful comments
    assert "#" in content

    # Verify default values are set
    assert '"pareidolia"' in content or "'pareidolia'" in content
    assert "standard" in content


def test_init_creates_prompts_directory(tmp_path: Path) -> None:
    """Test that init creates the prompts output directory."""
    # Run init
    result = run_init_command(["init"], cwd=tmp_path)
    assert result.returncode == 0

    # Verify prompts directory exists
    prompts_dir = tmp_path / "prompts"
    assert prompts_dir.exists()
    assert prompts_dir.is_dir()

    # Verify it has a .gitignore
    gitignore = prompts_dir / ".gitignore"
    assert gitignore.exists()


def test_init_example_files_have_valid_content(tmp_path: Path) -> None:
    """Test that created example files have valid, non-empty content."""
    # Run init
    result = run_init_command(["init"], cwd=tmp_path)
    assert result.returncode == 0

    pareidolia_dir = tmp_path / "pareidolia"

    # Check persona example
    persona_file = pareidolia_dir / "personas" / "researcher.md"
    assert persona_file.exists()
    persona_content = persona_file.read_text()
    assert len(persona_content) > 0
    assert "researcher" in persona_content.lower()

    # Check action example
    action_file = pareidolia_dir / "actions" / "analyze.md.j2"
    assert action_file.exists()
    action_content = action_file.read_text()
    assert len(action_content) > 0
    # Should contain Jinja2 template syntax
    assert "{{" in action_content or "{%" in action_content

    # Check example file
    example_file = pareidolia_dir / "examples" / "analysis-output.md"
    assert example_file.exists()
    example_content = example_file.read_text()
    assert len(example_content) > 0

    # Check templates README
    templates_readme = pareidolia_dir / "templates" / "README.md"
    assert templates_readme.exists()
    templates_content = templates_readme.read_text()
    assert len(templates_content) > 0
    assert "template" in templates_content.lower()


def test_init_directory_structure_is_complete(tmp_path: Path) -> None:
    """Test that init creates all expected directories."""
    # Run init
    result = run_init_command(["init"], cwd=tmp_path)
    assert result.returncode == 0

    pareidolia_dir = tmp_path / "pareidolia"

    # Verify all expected directories exist
    # Verify all expected directories exist
    expected_dirs = [
        pareidolia_dir,
        pareidolia_dir / "personas",
        pareidolia_dir / "actions",
        pareidolia_dir / "examples",
        pareidolia_dir / "templates",
        tmp_path / "prompts",
    ]
    for expected_dir in expected_dirs:
        assert expected_dir.exists(), f"Expected {expected_dir} to exist"
        assert expected_dir.is_dir(), f"Expected {expected_dir} to be a directory"


def test_init_nested_directory_creation(tmp_path: Path) -> None:
    """Test init can create nested directory structure."""
    # Run init with nested path
    nested_path = "projects/new-project"
    result = run_init_command(["init", nested_path], cwd=tmp_path)

    # Verify success
    assert result.returncode == 0

    # Verify nested directories created
    project_dir = tmp_path / "projects" / "new-project"
    assert project_dir.exists()

    # Verify structure created in nested location
    config_file = project_dir / ".pareidolia.toml"
    assert config_file.exists()

    pareidolia_dir = project_dir / "pareidolia"
    assert pareidolia_dir.exists()


def test_init_preserves_existing_directories(tmp_path: Path) -> None:
    """Test that init works when target directory already exists."""
    # Create target directory with some content
    project_dir = tmp_path / "existing-project"
    project_dir.mkdir()
    (project_dir / "README.md").write_text("# Existing Project\n")

    # Run init in existing directory
    result = run_init_command(["init", "existing-project"], cwd=tmp_path)

    # Verify success
    assert result.returncode == 0

    # Verify existing file preserved
    readme = project_dir / "README.md"
    assert readme.exists()
    assert "Existing Project" in readme.read_text()

    # Verify new files created
    config_file = project_dir / ".pareidolia.toml"
    assert config_file.exists()

    pareidolia_dir = project_dir / "pareidolia"
    assert pareidolia_dir.exists()


def test_init_output_messages(tmp_path: Path) -> None:
    """Test that init provides appropriate user feedback messages."""
    # Run init
    result = run_init_command(["init"], cwd=tmp_path)
    assert result.returncode == 0

    output = result.stdout

    # Verify progress messages
    assert "✓" in output or "Created" in output

    # Verify completion message
    assert "successfully" in output.lower()

    # Verify next steps are provided
    assert "Next steps" in output or "next" in output.lower()


def test_init_no_scaffold_skips_gitignore(tmp_path: Path) -> None:
    """Test that --no-scaffold doesn't create .gitignore."""
    # Run init with --no-scaffold
    result = run_init_command(["init", "--no-scaffold"], cwd=tmp_path)
    assert result.returncode == 0

    # Verify prompts directory doesn't exist (so no .gitignore)
    prompts_dir = tmp_path / "prompts"
    assert not prompts_dir.exists()

    gitignore = prompts_dir / ".gitignore"
    assert not gitignore.exists()
