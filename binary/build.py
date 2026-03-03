#!/usr/bin/env python3
# Copyright (c) 2026 Ramin Firoozye
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Build script for creating standalone executables using cx_Freeze."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Ensure binary directory is on path so config is found (e.g. when run as python binary/build.py)
sys.path.insert(0, str(Path(__file__).parent.resolve()))
# Parent (enveloper-py) for optional imports
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
    """Convert architecture name to cx_Freeze-compatible name."""
    arch_map = {
        "mac": {"x86_64": "x86_64", "arm64": "arm64"},
        "linux": {"x86_64": "x86_64", "arm64": "aarch64", "aarch64": "aarch64"},
        "win": {"x86_64": "x86_64", "arm64": "arm64"},
    }
    return arch_map.get(platform, {}).get(arch, arch)


def check_cx_freeze() -> bool:
    """Check if cx_Freeze is installed."""
    try:
        subprocess.run(
            [sys.executable, "-m", "cx_Freeze", "--version"],
            check=True,
            capture_output=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def install_cx_freeze() -> None:
    """Install cx_Freeze using uv."""
    print("Installing cx_Freeze using uv...")
    binary_dir = Path(__file__).parent.resolve()
    
    subprocess.run(
        ["uv", "pip", "install", "cx-freeze"],
        cwd=str(binary_dir),
        check=True,
    )


def build_macos(
    arch: str,
    version: str = VERSION,
    icon_path: Path = ICON_PATH,
) -> Path:
    """Build macOS executable using cx_Freeze."""
    print(f"Building macOS {arch} executable...")
    
    arch_name = get_arch_for_platform("mac", arch)
    output_dir = DIST_DIR / f"{PROJECT_NAME}-{version}-macos-{arch}"
    output_dir.mkdir(parents=True, exist_ok=True)

    # cx_Freeze setup script
    setup_script = BASE_DIR / "setup_cxfreeze.py"
    
    build_args = [
        sys.executable,
        str(setup_script),
        "build_exe",
        f"--build-exe={output_dir}",
    ]

    subprocess.run(build_args, check=True)

    # Create zip archive
    zip_path = output_dir.parent / f"{PROJECT_NAME}-{version}-macos-{arch}.zip"
    subprocess.run(
        ["zip", "-r", str(zip_path), output_dir.name],
        cwd=output_dir.parent,
        check=True,
    )

    return zip_path


def build_linux(
    arch: str,
    version: str = VERSION,
    icon_path: Path = ICON_PATH,
) -> Path:
    """Build Linux executable using cx_Freeze."""
    print(f"Building Linux {arch} executable...")

    arch_name = get_arch_for_platform("linux", arch)
    output_dir = DIST_DIR / f"{PROJECT_NAME}-{version}-linux-{arch}"
    output_dir.mkdir(parents=True, exist_ok=True)

    # cx_Freeze setup script
    setup_script = BASE_DIR / "setup_cxfreeze.py"
    
    build_args = [
        sys.executable,
        str(setup_script),
        "build_exe",
        f"--build-exe={output_dir}",
    ]

    subprocess.run(build_args, check=True)

    # Create zip archive
    zip_path = output_dir.parent / f"{PROJECT_NAME}-{version}-linux-{arch}.zip"
    subprocess.run(
        ["zip", "-r", str(zip_path), output_dir.name],
        cwd=output_dir.parent,
        check=True,
    )

    return zip_path


def build_windows(
    arch: str,
    version: str = VERSION,
    icon_path: Path = ICON_PATH,
) -> Path:
    """Build Windows executable using cx_Freeze."""
    print(f"Building Windows {arch} executable...")

    arch_name = get_arch_for_platform("win", arch)
    output_dir = DIST_DIR / f"{PROJECT_NAME}-{version}-windows-{arch}"
    output_dir.mkdir(parents=True, exist_ok=True)

    # cx_Freeze setup script
    setup_script = BASE_DIR / "setup_cxfreeze.py"
    
    build_args = [
        sys.executable,
        str(setup_script),
        "build_exe",
        f"--build-exe={output_dir}",
    ]

    subprocess.run(build_args, check=True)

    return output_dir


def build_all(
    platforms: list[str] | None = None,
    arch_filter: str | None = None,
) -> list[Path]:
    """Build for all specified platforms and architectures."""
    if platforms is None:
        platforms = list(PLATFORMS.keys())

    built_files = []

    for platform in platforms:
        config = PLATFORMS[platform]
        archs = config["architectures"]
        if arch_filter is not None:
            # Normalize aarch64 <-> arm64 for linux
            if platform == "linux" and arch_filter == "arm64":
                archs = [a for a in archs if a in ("arm64", "aarch64")]
            else:
                archs = [a for a in archs if a == arch_filter]
        for arch in archs:
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
        "--dmg",
        action="store_true",
        help="(macOS only) Also build .pkg and .dmg installer for double-click install to /usr/local",
    )

    args = parser.parse_args()

    # Check/install cx_Freeze
    if not check_cx_freeze():
        install_cx_freeze()

    icon_path = Path(args.icon)

    if args.platform == "all":
        platforms = list(PLATFORMS.keys())
    else:
        platforms = [args.platform]

    print(f"Building for platforms: {platforms}" + (f", arch: {args.arch}" if args.arch else ""))
    built_files = build_all(platforms, arch_filter=args.arch)

    # Optionally build macOS .pkg and .dmg installers for double-click install to /usr/local
    if args.dmg and "mac" in platforms:
        from mac_installer import build_pkg_and_dmg
        version = getattr(args, "version", VERSION)
        archs = PLATFORMS["mac"]["architectures"]
        if args.arch:
            archs = [a for a in archs if a == args.arch]
        for arch in archs:
            bundle_dir = DIST_DIR / f"{PROJECT_NAME}-{version}-macos-{arch}"
            if bundle_dir.exists():
                _, dmg_path = build_pkg_and_dmg(bundle_dir, version=version, arch=arch)
                built_files.append(dmg_path)

    print("\nBuild complete!")
    for f in built_files:
        print(f"  {f}")


if __name__ == "__main__":
    main()