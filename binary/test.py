#!/usr/bin/env python3
# Copyright (c) 2026 Ramin Firoozye
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Test script for built binaries."""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DIST_DIR, PROJECT_NAME, VERSION


def test_binary(binary_path: Path) -> bool:
    """Test a single binary."""
    print(f"Testing {binary_path}...")

    # Test --version
    try:
        result = subprocess.run(
            [str(binary_path), "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            print(f"  FAIL: --version returned {result.returncode}")
            print(f"  stderr: {result.stderr}")
            return False
        print(f"  OK: --version works (output: {result.stdout.strip()})")
    except subprocess.TimeoutExpired:
        print("  FAIL: --version timed out")
        return False
    except Exception as e:
        print(f"  FAIL: {e}")
        return False

    # Test --help
    try:
        result = subprocess.run(
            [str(binary_path), "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            print(f"  FAIL: --help returned {result.returncode}")
            return False
        print("  OK: --help works")
    except subprocess.TimeoutExpired:
        print("  FAIL: --help timed out")
        return False
    except Exception as e:
        print(f"  FAIL: {e}")
        return False

    return True


def test_macos_binaries() -> list[Path]:
    """Find and test macOS binaries."""
    binaries = []
    for arch in ["x86_64", "arm64"]:
        zip_path = DIST_DIR / f"{PROJECT_NAME}-{VERSION}-macos-{arch}.zip"
        if zip_path.exists():
            binaries.append(zip_path)
    return binaries


def test_linux_binaries() -> list[Path]:
    """Find and test Linux binaries."""
    binaries = []
    for arch in ["x86_64", "arm64", "aarch64"]:
        zip_path = DIST_DIR / f"{PROJECT_NAME}-{VERSION}-linux-{arch}.zip"
        if zip_path.exists():
            binaries.append(zip_path)
    return binaries


def test_windows_binaries() -> list[Path]:
    """Find and test Windows binaries."""
    binaries = []
    for arch in ["x86_64", "arm64"]:
        dir_path = DIST_DIR / f"{PROJECT_NAME}-{VERSION}-windows-{arch}"
        if dir_path.exists():
            exe_path = dir_path / f"{PROJECT_NAME}.exe"
            if exe_path.exists():
                binaries.append(exe_path)
    return binaries


def test_all() -> bool:
    """Test all built binaries."""
    all_passed = True

    # Test macOS binaries
    print("\n=== Testing macOS Binaries ===")
    for zip_path in test_macos_binaries():
        print(f"\nTesting {zip_path.name}...")
        # Extract and test
        extract_dir = DIST_DIR / "test_extract"
        extract_dir.mkdir(exist_ok=True)
        subprocess.run(
            ["unzip", "-o", str(zip_path), "-d", str(extract_dir)],
            check=True,
        )
        # Find the binary
        binary_path = extract_dir / PROJECT_NAME
        if binary_path.exists():
            if not test_binary(binary_path):
                all_passed = False
        else:
            print(f"  FAIL: Binary not found in {extract_dir}")
            all_passed = False
        # Cleanup
        shutil.rmtree(extract_dir)

    # Test Linux binaries
    print("\n=== Testing Linux Binaries ===")
    for zip_path in test_linux_binaries():
        print(f"\nTesting {zip_path.name}...")
        # Extract and test
        extract_dir = DIST_DIR / "test_extract"
        extract_dir.mkdir(exist_ok=True)
        subprocess.run(
            ["unzip", "-o", str(zip_path), "-d", str(extract_dir)],
            check=True,
        )
        # Find the binary
        binary_path = extract_dir / PROJECT_NAME
        if binary_path.exists():
            # Make executable
            binary_path.chmod(0o755)
            if not test_binary(binary_path):
                all_passed = False
        else:
            print(f"  FAIL: Binary not found in {extract_dir}")
            all_passed = False
        # Cleanup
        shutil.rmtree(extract_dir)

    # Test Windows binaries
    print("\n=== Testing Windows Binaries ===")
    for exe_path in test_windows_binaries():
        if not test_binary(exe_path):
            all_passed = False

    return all_passed


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Test enveloper binaries")
    parser.add_argument(
        "--binary",
        "-b",
        default=None,
        help="Specific binary to test",
    )
    parser.add_argument(
        "--platform",
        "-p",
        choices=["mac", "linux", "win"],
        default=None,
        help="Platform to test (default: all)",
    )

    args = parser.parse_args()

    if args.binary:
        binary_path = Path(args.binary)
        if not binary_path.exists():
            print(f"Binary not found: {binary_path}")
            sys.exit(1)
        if test_binary(binary_path):
            print("\nTest passed!")
            sys.exit(0)
        else:
            print("\nTest failed!")
            sys.exit(1)

    if test_all():
        print("\n=== All tests passed! ===")
        sys.exit(0)
    else:
        print("\n=== Some tests failed! ===")
        sys.exit(1)


if __name__ == "__main__":
    main()