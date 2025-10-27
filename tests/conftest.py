"""Pytest configuration and shared fixtures."""

import shutil
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests.

    Yields:
        Path to temporary directory
    """
    temp_path = Path(tempfile.mkdtemp())
    try:
        yield temp_path
    finally:
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
    (pareidolia_root / "persona").mkdir(parents=True)
    (pareidolia_root / "action").mkdir(parents=True)
    (pareidolia_root / "example").mkdir(parents=True)

    # Create sample persona
    persona_file = pareidolia_root / "persona" / "researcher.md"
    persona_file.write_text(
        "You are an expert researcher with deep analytical skills.\n"
        "You approach problems methodically and thoroughly.\n"
    )

    # Create sample action
    action_file = pareidolia_root / "action" / "research.md.j2"
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
    example_file = pareidolia_root / "example" / "report-format.md"
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
        '[export]\n'
        'tool = "standard"\n'
        'output_dir = "prompts"\n'
    )

    return project_root
