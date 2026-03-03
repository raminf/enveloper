#!/usr/bin/env python3
# Copyright (c) 2026 Ramin Firoozye
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Build macOS .pkg and .dmg installers.

Produces a single DMG file that users can double-click. The DMG contains a .pkg
installer which installs the enveloper CLI to /usr/local/enveloper/ and creates
/usr/local/bin/enveloper so it is runnable from the terminal.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.resolve()))
from config import DIST_DIR, PROJECT_NAME, VERSION

# Install prefix for the CLI (well-known location on PATH)
INSTALL_PREFIX = "/usr/local"
INSTALL_DIR = f"{INSTALL_PREFIX}/enveloper"
BIN_SYMLINK = f"{INSTALL_PREFIX}/bin/enveloper"
PKG_ID = "com.enveloper.cli"


def build_pkg(
    bundle_dir: Path,
    version: str = VERSION,
    arch: str = "arm64",
    output_dir: Path | None = None,
) -> Path:
    """Build a .pkg installer that installs the bundle to /usr/local/enveloper and links /usr/local/bin/enveloper."""
    if output_dir is None:
        output_dir = bundle_dir.parent
    pkg_name = f"{PROJECT_NAME}-{version}-macos-{arch}.pkg"
    pkg_path = output_dir / pkg_name

    with tempfile.TemporaryDirectory(prefix="enveloper-pkg-") as tmp:
        root = Path(tmp) / "root"
        scripts = Path(tmp) / "scripts"
        (root / "usr/local/enveloper").mkdir(parents=True)
        scripts.mkdir()

        # Copy bundle contents into usr/local/enveloper
        for item in bundle_dir.iterdir():
            dest = root / "usr/local/enveloper" / item.name
            if item.is_dir():
                shutil.copytree(item, dest, symlinks=True)
            else:
                shutil.copy2(item, dest)

        # postinstall: create symlink so `enveloper` is on PATH
        postinstall = scripts / "postinstall"
        postinstall.write_text(
            """#!/bin/bash
set -e
# Ensure /usr/local/bin exists (default on macOS but safe to create)
mkdir -p /usr/local/bin
# Symlink so 'enveloper' is runnable from terminal
ln -sf /usr/local/enveloper/enveloper /usr/local/bin/enveloper
"""
        )
        postinstall.chmod(0o755)

        # Build component pkg with pkgbuild
        component_pkg = Path(tmp) / "enveloper-component.pkg"
        subprocess.run(
            [
                "pkgbuild",
                "--root",
                str(root),
                "--scripts",
                str(scripts),
                "--identifier",
                PKG_ID,
                "--version",
                version,
                "--install-location",
                "/",
                str(component_pkg),
            ],
            check=True,
        )

        # Build product (flat pkg) with productbuild
        subprocess.run(
            [
                "productbuild",
                "--package",
                str(component_pkg),
                "--identifier",
                PKG_ID,
                "--version",
                version,
                str(pkg_path),
            ],
            check=True,
        )

    print(f"Created pkg: {pkg_path}")
    return pkg_path


def build_dmg(
    pkg_path: Path,
    version: str = VERSION,
    arch: str = "arm64",
    output_dir: Path | None = None,
) -> Path:
    """Build a .dmg disk image containing the .pkg for double-click install."""
    if output_dir is None:
        output_dir = pkg_path.parent
    dmg_name = f"{PROJECT_NAME}-{version}-macos-{arch}.dmg"
    dmg_path = output_dir / dmg_name

    with tempfile.TemporaryDirectory(prefix="enveloper-dmg-") as tmp:
        mount_point = Path(tmp) / "dmg"
        mount_point.mkdir()
        # Copy pkg into a folder that will be the DMG contents
        shutil.copy2(pkg_path, mount_point / pkg_path.name)

        # Create read-only DMG with hdiutil
        temp_dmg = Path(tmp) / "temp.dmg"
        subprocess.run(
            [
                "hdiutil",
                "create",
                "-volname",
                f"Install {PROJECT_NAME} {version}",
                "-srcfolder",
                str(mount_point),
                "-ov",
                "-format",
                "UDZO",
                str(temp_dmg),
            ],
            check=True,
        )
        shutil.copy2(temp_dmg, dmg_path)

    print(f"Created dmg: {dmg_path}")
    return dmg_path


def build_pkg_and_dmg(
    bundle_dir: Path,
    version: str = VERSION,
    arch: str = "arm64",
) -> tuple[Path, Path]:
    """Build both .pkg and .dmg for the given bundle directory."""
    pkg_path = build_pkg(bundle_dir, version=version, arch=arch)
    dmg_path = build_dmg(pkg_path, version=version, arch=arch, output_dir=bundle_dir.parent)
    return pkg_path, dmg_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build macOS .pkg and .dmg installers for enveloper"
    )
    parser.add_argument(
        "--bundle-dir",
        type=Path,
        default=None,
        help=f"Path to the cx_Freeze bundle (default: {DIST_DIR}/enveloper-{{version}}-macos-{{arch}})",
    )
    parser.add_argument("--version", "-v", default=VERSION, help="Version string")
    parser.add_argument(
        "--arch",
        "-a",
        choices=["x86_64", "arm64"],
        default="arm64",
        help="Architecture (default: arm64)",
    )
    parser.add_argument(
        "--pkg-only",
        action="store_true",
        help="Only build .pkg, do not create .dmg",
    )
    parser.add_argument(
        "--dmg-only",
        action="store_true",
        help="Only build .dmg from existing .pkg",
    )
    args = parser.parse_args()

    bundle_dir = args.bundle_dir
    if bundle_dir is None:
        bundle_dir = DIST_DIR / f"{PROJECT_NAME}-{args.version}-macos-{args.arch}"
    if not bundle_dir.is_dir():
        print(f"Error: bundle directory not found: {bundle_dir}", file=sys.stderr)
        print("Run the Mac build first, e.g.: make build-mac-arm", file=sys.stderr)
        sys.exit(1)

    if args.dmg_only:
        pkg_path = bundle_dir.parent / f"{PROJECT_NAME}-{args.version}-macos-{args.arch}.pkg"
        if not pkg_path.exists():
            print(f"Error: pkg not found: {pkg_path}", file=sys.stderr)
            sys.exit(1)
        build_dmg(pkg_path, version=args.version, arch=args.arch)
    elif args.pkg_only:
        build_pkg(bundle_dir, version=args.version, arch=args.arch)
    else:
        build_pkg_and_dmg(bundle_dir, version=args.version, arch=args.arch)


if __name__ == "__main__":
    main()
