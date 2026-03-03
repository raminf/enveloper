#!/usr/bin/env python3
# Copyright (c) 2026 Ramin Firoozye
# SPDX-License-Identifier: AGPL-3.0-or-later

"""cx_Freeze setup script for building enveloper standalone executables."""

from __future__ import annotations

import sys
from pathlib import Path

# Binary directory (this script lives in binary/)
BINARY_DIR = Path(__file__).parent.resolve()
# Project root (enveloper-py)
BASE_DIR = BINARY_DIR.parent
# Source directory (enveloper-py/src) - must be on path so "enveloper" package is found
SRC_DIR = BASE_DIR / "src"
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(SRC_DIR))

from cx_Freeze import Executable, setup

# Get the project version from pyproject.toml
import re
pyproject = BASE_DIR / "pyproject.toml"
version = "0.1.16"
if pyproject.exists():
    match = re.search(r'^version\s*=\s*"([^"]+)"', pyproject.read_text(), re.MULTILINE)
    if match:
        version = match.group(1)

# Create a simple wrapper script that imports the CLI directly
wrapper_script = SRC_DIR / "enveloper" / "__main__.py"

# Icon: prefer binary/icon (copy of media/envelope.svg), else media/envelope.svg
# Do not add enveloper/__main__.py to include_files - it would create a directory
# "enveloper" in the build root and clash with the executable named "enveloper"
icon_src = BINARY_DIR / "icon" / "envelope.svg"
if not icon_src.exists():
    icon_src = BASE_DIR / "media" / "envelope.svg"
include_files = []
if icon_src.exists():
    include_files.append((str(icon_src), "icon/envelope.svg"))

setup(
    name="enveloper",
    version=version,
    description="Manage .env secrets via system keychain with cloud store plugins.",
    executables=[
        Executable(
            script=str(wrapper_script),
            target_name="enveloper",
            base="console",
        ),
    ],
    options={
        "build_exe": {
            "packages": [
                "enveloper",
            ],
            "includes": [
                "enveloper.cli",
                "enveloper.stores",
            ],
            "excludes": [
                "tkinter",
                "unittest",
            ],
            "include_files": include_files,
            "optimize": 1,
        },
    },
)