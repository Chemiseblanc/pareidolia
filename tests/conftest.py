"""Pytest configuration and shared fixtures."""

import shutil
from collections.abc import Generator
from pathlib import Path

import pytest

# Test directory - gitignored and auto-cleaned
TEST_TMP_DIR = Path(__file__).parent.parent / ".test-tmp"


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_dir() -> Generator[None, None, None]:
    """Clean up test directory before and after all tests.

    This fixture runs automatically for the entire test session.
    It cleans up the test directory at the start and ensures cleanup
    on successful completion.
    """
    # Clean up before tests
    if TEST_TMP_DIR.exists():
        shutil.rmtree(TEST_TMP_DIR)
    TEST_TMP_DIR.mkdir(parents=True, exist_ok=True)

    yield

    # Clean up after successful test session
    if TEST_TMP_DIR.exists():
        shutil.rmtree(TEST_TMP_DIR)


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests in gitignored location.

    Each test gets its own subdirectory under .test-tmp/.
    The directory is cleaned up after the test completes.

    Yields:
        Path to temporary directory
    """
    import uuid

    # Create unique subdirectory for this test
    temp_path = TEST_TMP_DIR / str(uuid.uuid4())
    temp_path.mkdir(parents=True, exist_ok=True)

    try:
        yield temp_path
    finally:
        # Clean up this test's directory
        if temp_path.exists():
            shutil.rmtree(temp_path)


@pytest.fixture
def sample_project(temp_dir: Path) -> Path:
    """Create a sample project structure with test data.

    Args:
        temp_dir: Temporary directory fixture

    Returns:
        Path to project root
    """
    project_root = temp_dir / "test_project"
    pareidolia_root = project_root / "pareidolia"

    # Create directories
    (pareidolia_root / "personas").mkdir(parents=True)
    (pareidolia_root / "actions").mkdir(parents=True)
    (pareidolia_root / "examples").mkdir(parents=True)

    # Create sample persona
    persona_file = pareidolia_root / "personas" / "researcher.md"
    persona_file.write_text(
        "You are an expert researcher with deep analytical skills.\n"
        "You approach problems methodically and thoroughly.\n"
    )

    # Create sample action
    action_file = pareidolia_root / "actions" / "research.md.j2"
    action_file.write_text(
        "{{ persona }}\n\n"
        "Your task is to research the following topic and provide "
        "a comprehensive analysis.\n"
        "{% if examples %}\n"
        "Examples:\n"
        "{% for example in examples %}\n"
        "{{ example }}\n"
        "{% endfor %}\n"
        "{% endif %}\n"
    )

    # Create sample example
    example_file = pareidolia_root / "examples" / "report-format.md"
    example_file.write_text(
        "# Research Report Example\n\n"
        "## Overview\n"
        "Brief summary of findings.\n\n"
        "## Details\n"
        "In-depth analysis.\n"
    )

    # Create config file
    config_file = project_root / "pareidolia.toml"
    config_file.write_text(
        '[pareidolia]\n'
        'root = "pareidolia"\n\n'
        '[generate]\n'
        'tool = "standard"\n'
        'output_dir = "prompts"\n'
    )

    return project_root
