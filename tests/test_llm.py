# Copyright (c) 2026 Ramin Firoozye
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for the LLM/ directory: structure and required content for LLM/AI assistant guidance."""

from __future__ import annotations

from pathlib import Path

import pytest

# Repo root (parent of tests/)
REPO_ROOT = Path(__file__).resolve().parent.parent
LLM_DIR = REPO_ROOT / "LLM"
GUIDELINES_DIR = LLM_DIR / "guidelines"


def _read(path: Path) -> str:
    return path.read_text() if path.is_file() else ""


# ---------------------------------------------------------------------------
# Structure
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_llm_dir_exists():
    """LLM/ directory must exist."""
    assert LLM_DIR.is_dir(), "LLM/ directory must exist for LLM/AI assistant guidance"


@pytest.mark.unit
def test_llm_readme_exists():
    """LLM/README.md must exist."""
    readme = LLM_DIR / "README.md"
    assert readme.is_file(), "LLM/README.md must exist"


@pytest.mark.unit
def test_llm_guidelines_dir_exists():
    """LLM/guidelines/ directory must exist."""
    assert GUIDELINES_DIR.is_dir(), "LLM/guidelines/ must exist"


@pytest.mark.unit
def test_llm_guideline_files_exist():
    """Required guideline files must exist."""
    required = ["conventions.md", "testing.md", "examples.md", "mcp.md"]
    for name in required:
        path = GUIDELINES_DIR / name
        assert path.is_file(), f"LLM/guidelines/{name} must exist"


# ---------------------------------------------------------------------------
# LLM/README.md content
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_llm_readme_describes_enveloper():
    """LLM README must describe what enveloper is."""
    content = _read(LLM_DIR / "README.md")
    assert "enveloper" in content.lower()
    assert "keychain" in content.lower() or "secret" in content.lower()


@pytest.mark.unit
def test_llm_readme_has_repo_layout():
    """LLM README must include repository layout or structure."""
    content = _read(LLM_DIR / "README.md")
    assert "src" in content or "layout" in content.lower() or "tests" in content
    assert "examples" in content.lower()


@pytest.mark.unit
def test_llm_readme_has_commands():
    """LLM README must mention how to run tests or checks."""
    content = _read(LLM_DIR / "README.md")
    assert "pytest" in content or "make check" in content or "make test" in content
    assert "uv" in content


@pytest.mark.unit
def test_llm_readme_links_to_guidelines():
    """LLM README must link to guidelines (conventions, testing, examples)."""
    content = _read(LLM_DIR / "README.md")
    assert "guidelines" in content.lower()
    assert "conventions" in content.lower() or "testing" in content.lower() or "examples" in content.lower()


# ---------------------------------------------------------------------------
# Guideline content
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_llm_conventions_mention_uv():
    """Conventions must mention uv as package manager."""
    content = _read(GUIDELINES_DIR / "conventions.md")
    assert "uv" in content


@pytest.mark.unit
def test_llm_conventions_mention_python_version():
    """Conventions must mention Python version (e.g. 3.12)."""
    content = _read(GUIDELINES_DIR / "conventions.md")
    assert "3.12" in content or "python" in content.lower()


@pytest.mark.unit
def test_llm_testing_mention_pytest():
    """Testing guidelines must mention pytest."""
    content = _read(GUIDELINES_DIR / "testing.md")
    assert "pytest" in content


@pytest.mark.unit
def test_llm_testing_mention_markers():
    """Testing guidelines must mention unit/integration or markers."""
    content = _read(GUIDELINES_DIR / "testing.md")
    assert "unit" in content.lower() or "integration" in content.lower() or "marker" in content.lower()


@pytest.mark.unit
def test_llm_examples_mention_structure():
    """Examples guidelines must mention examples folder or structure."""
    content = _read(GUIDELINES_DIR / "examples.md")
    assert "examples" in content.lower()
    assert "README" in content or "readme" in content.lower()
