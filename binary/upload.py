#!/usr/bin/env python3
# Copyright (c) 2026 Ramin Firoozye
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Upload script for publishing binaries to GitHub Releases."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DIST_DIR, GITHUB_OWNER, GITHUB_REPO, PROJECT_NAME, VERSION


def check_gh_cli() -> bool:
    """Check if GitHub CLI is installed."""
    try:
        subprocess.run(
            ["gh", "--version"],
            capture_output=True,
            check=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def get_release(release_name: str) -> dict | None:
    """Get an existing release by tag name."""
    try:
        result = subprocess.run(
            ["gh", "release", "view", release_name, "--json", "id,tagName"],
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError:
        return None


def create_release(release_name: str, draft: bool = False) -> dict:
    """Create a new GitHub release."""
    print(f"Creating release: {release_name}")
    result = subprocess.run(
        [
            "gh", "release", "create",
            release_name,
            "--title", f"{PROJECT_NAME} v{VERSION}",
            "--notes", f"Release {PROJECT_NAME} version {VERSION}",
        ] + (["--draft"] if draft else []),
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


def upload_asset(release_name: str, asset_path: Path) -> bool:
    """Upload an asset to a GitHub release."""
    print(f"Uploading {asset_path.name}...")
    result = subprocess.run(
        [
            "gh", "release", "upload",
            release_name,
            str(asset_path),
            "--clobber",
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"Upload failed: {result.stderr}")
        return False
    print(f"Uploaded: {asset_path.name}")
    return True


def upload_all(release_name: str | None = None, draft: bool = False) -> bool:
    """Upload all binaries to GitHub Releases."""
    if release_name is None:
        release_name = f"v{VERSION}"

    # Check if GitHub CLI is installed
    if not check_gh_cli():
        print("GitHub CLI (gh) not found. Please install it:")
        print("  macOS: brew install gh")
        print("  Linux: https://github.com/cli/cli/blob/trunk/docs/install_linux.md")
        return False

    # Check if user is logged in
    try:
        subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            check=True,
        )
    except subprocess.CalledProcessError:
        print("Not logged in to GitHub. Please run:")
        print("  gh auth login")
        return False

    # Check if release exists
    release = get_release(release_name)
    if release is None:
        print(f"Release {release_name} not found. Creating...")
        release = create_release(release_name, draft)

    release_id = release.get("id", release_name)

    # Find all binaries
    uploaded = []
    failed = []

    # macOS binaries
    for arch in ["x86_64", "arm64"]:
        zip_path = DIST_DIR / f"{PROJECT_NAME}-{VERSION}-macos-{arch}.zip"
        if zip_path.exists():
            if upload_asset(release_name, zip_path):
                uploaded.append(str(zip_path))
            else:
                failed.append(str(zip_path))

    # Linux binaries
    for arch in ["x86_64", "arm64", "aarch64"]:
        zip_path = DIST_DIR / f"{PROJECT_NAME}-{VERSION}-linux-{arch}.zip"
        if zip_path.exists():
            if upload_asset(release_name, zip_path):
                uploaded.append(str(zip_path))
            else:
                failed.append(str(zip_path))

    # Windows binaries
    for arch in ["x86_64", "arm64"]:
        dir_path = DIST_DIR / f"{PROJECT_NAME}-{VERSION}-windows-{arch}"
        if dir_path.exists():
            exe_path = dir_path / f"{PROJECT_NAME}.exe"
            if exe_path.exists():
                if upload_asset(release_name, exe_path):
                    uploaded.append(str(exe_path))
                else:
                    failed.append(str(exe_path))

    # Summary
    print("\n=== Upload Summary ===")
    print(f"Uploaded: {len(uploaded)}")
    for f in uploaded:
        print(f"  ✓ {f}")
    if failed:
        print(f"Failed: {len(failed)}")
        for f in failed:
            print(f"  ✗ {f}")

    return len(failed) == 0


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Upload enveloper binaries to GitHub Releases")
    parser.add_argument(
        "--release",
        "-r",
        default=None,
        help="Release tag name (default: v<version>)",
    )
    parser.add_argument(
        "--draft",
        action="store_true",
        default=False,
        help="Create as draft (default: false)",
    )
    parser.add_argument(
        "--asset",
        "-a",
        default=None,
        help="Specific asset to upload",
    )

    args = parser.parse_args()

    if args.asset:
        asset_path = Path(args.asset)
        if not asset_path.exists():
            print(f"Asset not found: {asset_path}")
            sys.exit(1)

        release_name = args.release or f"v{VERSION}"
        if upload_asset(release_name, asset_path):
            print("\nUpload passed!")
            sys.exit(0)
        else:
            print("\nUpload failed!")
            sys.exit(1)

    if upload_all(args.release, args.draft):
        print("\n=== All uploads complete! ===")
        sys.exit(0)
    else:
        print("\n=== Some uploads failed! ===")
        sys.exit(1)


if __name__ == "__main__":
    main()