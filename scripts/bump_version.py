#!/usr/bin/env python3
"""Bump the version in pyproject.toml and src/enveloper/__init__.py."""

from __future__ import annotations

import re
import sys
from pathlib import Path

PYPROJECT = Path("pyproject.toml")
INIT = Path("src/enveloper/__init__.py")

VERSION_RE = re.compile(r'^version\s*=\s*"(\d+\.\d+\.\d+)"', re.MULTILINE)
INIT_RE = re.compile(r'^__version__\s*=\s*"(\d+\.\d+\.\d+)"', re.MULTILINE)


def bump(part: str) -> str:
    text = PYPROJECT.read_text()
    m = VERSION_RE.search(text)
    if not m:
        print("Could not find version in pyproject.toml", file=sys.stderr)
        sys.exit(1)

    old = m.group(1)
    major, minor, patch = (int(x) for x in old.split("."))

    if part == "major":
        major += 1
        minor = 0
        patch = 0
    elif part == "minor":
        minor += 1
        patch = 0
    elif part == "patch":
        patch += 1
    else:
        print(f"Unknown part: {part}. Use major, minor, or patch.", file=sys.stderr)
        sys.exit(1)

    new = f"{major}.{minor}.{patch}"

    PYPROJECT.write_text(VERSION_RE.sub(f'version = "{new}"', text))

    if INIT.exists():
        init_text = INIT.read_text()
        INIT.write_text(INIT_RE.sub(f'__version__ = "{new}"', init_text))

    return new


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: bump_version.py <major|minor|patch>", file=sys.stderr)
        sys.exit(1)
    new_version = bump(sys.argv[1])
    print(new_version)
