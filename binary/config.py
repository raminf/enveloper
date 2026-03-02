#!/usr/bin/env python3
# Copyright (c) 2026 Ramin Firoozye
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Configuration for binary builds."""

from __future__ import annotations

import os
import re
from pathlib import Path


def get_version() -> str:
    """Get version from pyproject.toml."""
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    content = pyproject_path.read_text()
    match = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
    if match:
        return match.group(1)
    raise ValueError("Could not find version in pyproject.toml")


def get_project_name() -> str:
    """Get project name from pyproject.toml."""
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    content = pyproject_path.read_text()
    match = re.search(r'^name\s*=\s*"([^"]+)"', content, re.MULTILINE)
    if match:
        return match.group(1)
    raise ValueError("Could not find project name in pyproject.toml")


# Configuration
VERSION = get_version()
PROJECT_NAME = get_project_name()

# Directories
BASE_DIR = Path(__file__).parent.resolve()
BUILD_DIR = BASE_DIR / "build"
DIST_DIR = BASE_DIR / "dist"
RELEASES_DIR = BASE_DIR / "releases"
ICONS_DIR = BASE_DIR / "icon"
CERTS_DIR = BASE_DIR / "certs"

# Ensure directories exist
for dir_path in [BUILD_DIR, DIST_DIR, RELEASES_DIR, ICONS_DIR, CERTS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# Icon path
ICON_PATH = ICONS_DIR / "envelope.svg"

# GitHub Releases configuration
GITHUB_OWNER = os.environ.get("GITHUB_OWNER", "raminf")
GITHUB_REPO = os.environ.get("GITHUB_REPO", "enveloper")

# Python version for building
PYTHON_VERSION = "3.12"

# Supported platforms and architectures
PLATFORMS = {
    "mac": {
        "name": "macOS",
        "architectures": ["x86_64", "arm64"],
        "formats": ["dir", "zip", "pkg"],
        "installer": "pkg",
    },
    "linux": {
        "name": "Linux",
        "architectures": ["x86_64", "arm64", "aarch64"],
        "formats": ["dir", "zip", "deb", "rpm"],
        "installer": "deb",
    },
    "win": {
        "name": "Windows",
        "architectures": ["x86_64", "arm64"],
        "formats": ["dir", "zip", "msi"],
        "installer": "msi",
    },
}

# PyInstaller options
PYINSTALLER_OPTIONS = {
    "onefile": True,
    "console": True,
    "strip": False,
    "upx": True,
    "upx_dir": None,
    "clean_build": True,
    "debug": False,
    "version_file": None,
}

# Homebrew configuration
HOMEBREW_TAP_OWNER = "raminf"
HOMEBREW_TAP_REPO = "homebrew-tap"
HOMEBREW_FORMULA_NAME = f"{PROJECT_NAME}.rb"

# Signing configuration
SIGNING = {
    "mac": {
        "enabled": False,
        "identity": "Developer ID Application",
        "keychain": None,
    },
    "win": {
        "enabled": False,
        "cert_path": None,
        "cert_password": None,
    },
}