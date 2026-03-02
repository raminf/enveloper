#!/usr/bin/env python3
# Copyright (c) 2026 Ramin Firoozye
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Build script for creating standalone executables using PyInstaller."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    BASE_DIR,
    BUILD_DIR,
    DIST_DIR,
    ICON_PATH,
    PLATFORMS,
    PROJECT_NAME,
    PYTHON_VERSION,
    VERSION,
)


def get_arch_for_platform(platform: str, arch: str) -> str:
    """Convert architecture name to PyInstaller-compatible name."""
    arch_map = {
        "mac": {"x86_64": "x86_64", "arm64": "arm64"},
        "linux": {"x86_64": "x86_64", "arm64": "aarch64", "aarch64": "aarch64"},
        "win": {"x86_64": "x86_64", "arm64": "arm64"},
    }
    return arch_map.get(platform, {}).get(arch, arch)


def check_pyinstaller() -> bool:
    """Check if PyInstaller is installed."""
    try:
        subprocess.run(
            [sys.executable, "-m", "PyInstaller", "--version"],
            check=True,
            capture_output=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def install_pyinstaller() -> None:
    """Install PyInstaller."""
    print("Installing PyInstaller...")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "pyinstaller"],
        check=True,
    )


def get_python_executable(version: str) -> Path:
    """Get the Python executable for the specified version."""
    # Try pyenv first
    pyenv_path = Path.home() / ".pyenv" / "versions" / version / "bin" / "python"
    if pyenv_path.exists():
        return pyenv_path

    # Try system python3.x
    python_path = Path(f"/usr/local/bin/python{version}")
    if python_path.exists():
        return python_path

    python_path = Path(f"/opt/homebrew/bin/python{version}")
    if python_path.exists():
        return python_path

    # Fall back to current python
    return Path(sys.executable)


def build_macos(
    arch: str,
    version: str = VERSION,
    icon_path: Path = ICON_PATH,
    onefile: bool = True,
    console: bool = True,
) -> Path:
    """Build macOS executable."""
    print(f"Building macOS {arch} executable...")
    
    arch_name = get_arch_for_platform("mac", arch)
    output_dir = DIST_DIR / f"{PROJECT_NAME}-{version}-macos-{arch}"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Build options
    build_args = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name",
        PROJECT_NAME,
        "--distpath",
        str(output_dir),
        "--workpath",
        str(BUILD_DIR / f"macos-{arch}"),
        "--specpath",
        str(BUILD_DIR),
    ]

    if icon_path.exists():
        build_args.extend(["--icon", str(icon_path)])

    if onefile:
        build_args.append("--onefile")
    else:
        build_args.append("--onedir")

    if not console:
        build_args.append("--windowed")

    # Add entry point
    build_args.append(str(BASE_DIR.parent / "src" / "enveloper" / "__main__.py"))

    # Run PyInstaller
    subprocess.run(build_args, check=True)

    # Create zip archive
    zip_path = output_dir.parent / f"{PROJECT_NAME}-{version}-macos-{arch}.zip"
    subprocess.run(
        ["zip", "-r", str(zip_path), PROJECT_NAME],
        cwd=output_dir,
        check=True,
    )

    return zip_path


def build_linux(
    arch: str,
    version: str = VERSION,
    icon_path: Path = ICON_PATH,
    onefile: bool = True,
    console: bool = True,
) -> Path:
    """Build Linux executable."""
    print(f"Building Linux {arch} executable...")

    arch_name = get_arch_for_platform("linux", arch)
    output_dir = DIST_DIR / f"{PROJECT_NAME}-{version}-linux-{arch}"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Build options
    build_args = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name",
        PROJECT_NAME,
        "--distpath",
        str(output_dir),
        "--workpath",
        str(BUILD_DIR / f"linux-{arch}"),
        "--specpath",
        str(BUILD_DIR),
    ]

    if icon_path.exists():
        build_args.extend(["--icon", str(icon_path)])

    if onefile:
        build_args.append("--onefile")
    else:
        build_args.append("--onedir")

    if not console:
        build_args.append("--windowed")

    # Add entry point
    build_args.append(str(BASE_DIR.parent / "src" / "enveloper" / "__main__.py"))

    # Run PyInstaller
    subprocess.run(build_args, check=True)

    # Create zip archive
    zip_path = output_dir.parent / f"{PROJECT_NAME}-{version}-linux-{arch}.zip"
    subprocess.run(
        ["zip", "-r", str(zip_path), PROJECT_NAME],
        cwd=output_dir,
        check=True,
    )

    return zip_path


def build_windows(
    arch: str,
    version: str = VERSION,
    icon_path: Path = ICON_PATH,
    onefile: bool = True,
    console: bool = True,
) -> Path:
    """Build Windows executable."""
    print(f"Building Windows {arch} executable...")

    arch_name = get_arch_for_platform("win", arch)
    output_dir = DIST_DIR / f"{PROJECT_NAME}-{version}-windows-{arch}"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Build options
    build_args = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name",
        PROJECT_NAME,
        "--distpath",
        str(output_dir),
        "--workpath",
        str(BUILD_DIR / f"windows-{arch}"),
        "--specpath",
        str(BUILD_DIR),
    ]

    if icon_path.exists():
        build_args.extend(["--icon", str(icon_path)])

    if onefile:
        build_args.append("--onefile")
    else:
        build_args.append("--onedir")

    if not console:
        build_args.append("--windowed")

    # Add entry point
    build_args.append(str(BASE_DIR.parent / "src" / "enveloper" / "__main__.py"))

    # Run PyInstaller
    subprocess.run(build_args, check=True)

    return output_dir


def build_all(platforms: list[str] | None = None) -> list[Path]:
    """Build for all specified platforms."""
    if platforms is None:
        platforms = list(PLATFORMS.keys())

    built_files = []

    for platform in platforms:
        config = PLATFORMS[platform]
        for arch in config["architectures"]:
            if platform == "mac":
                built_files.append(build_macos(arch))
            elif platform == "linux":
                built_files.append(build_linux(arch))
            elif platform == "win":
                built_files.append(build_windows(arch))

    return built_files


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Build enveloper binaries")
    parser.add_argument(
        "--platform",
        "-p",
        choices=["mac", "linux", "win", "all"],
        default="all",
        help="Platform to build for (default: all)",
    )
    parser.add_argument(
        "--arch",
        "-a",
        choices=["x86_64", "arm64"],
        default=None,
        help="Architecture to build for (default: all for platform)",
    )
    parser.add_argument(
        "--version",
        "-v",
        default=VERSION,
        help="Version to build (default: from pyproject.toml)",
    )
    parser.add_argument(
        "--icon",
        "-i",
        default=str(ICON_PATH),
        help="Icon file path",
    )
    parser.add_argument(
        "--onefile",
        action="store_true",
        default=True,
        help="Build as single file (default)",
    )
    parser.add_argument(
        "--onedir",
        action="store_true",
        default=False,
        help="Build as directory",
    )
    parser.add_argument(
        "--console",
        action="store_true",
        default=True,
        help="Build with console (default)",
    )
    parser.add_argument(
        "--windowed",
        action="store_true",
        default=False,
        help="Build without console",
    )

    args = parser.parse_args()

    # Check/install PyInstaller
    if not check_pyinstaller():
        install_pyinstaller()

    # Set build options
    onefile = not args.onedir
    console = not args.windowed
    icon_path = Path(args.icon)

    if args.platform == "all":
        platforms = list(PLATFORMS.keys())
    else:
        platforms = [args.platform]

    print(f"Building for platforms: {platforms}")
    built_files = build_all(platforms)

    print("\nBuild complete!")
    for f in built_files:
        print(f"  {f}")


if __name__ == "__main__":
    main()