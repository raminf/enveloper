#!/usr/bin/env python3
# Copyright (c) 2026 Ramin Firoozye
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Homebrew formula generation script."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DIST_DIR, GITHUB_OWNER, GITHUB_REPO, PROJECT_NAME, VERSION


def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def generate_formula() -> str:
    """Generate Homebrew formula for enveloper."""
    # Get the latest release info from GitHub
    try:
        result = subprocess.run(
            ["gh", "release", "view", f"v{VERSION}", "--json", "assets"],
            capture_output=True,
            text=True,
            check=True,
        )
        release = json.loads(result.stdout)
        assets = release.get("assets", [])
    except subprocess.CalledProcessError:
        assets = []

    # Find macOS arm64 bottle (preferred for modern Macs)
    arm64_asset = None
    x86_64_asset = None

    for asset in assets:
        if asset.get("name") == f"{PROJECT_NAME}-{VERSION}-macos-arm64.zip":
            arm64_asset = asset
        elif asset.get("name") == f"{PROJECT_NAME}-{VERSION}-macos-x86_64.zip":
            x86_64_asset = asset

    # Calculate SHA256 hashes
    arm64_sha256 = None
    x86_64_sha256 = None

    if arm64_asset:
        asset_name = arm64_asset["name"]
        asset_url = arm64_asset["url"]
        arm64_sha256 = calculate_sha256(DIST_DIR / asset_name)

    if x86_64_asset:
        asset_name = x86_64_asset["name"]
        asset_url = x86_64_asset["url"]
        x86_64_sha256 = calculate_sha256(DIST_DIR / asset_name)

    # Generate formula
    formula = f'''# Copyright (c) 2026 Ramin Firoozye
# SPDX-License-Identifier: AGPL-3.0-or-later

class {PROJECT_NAME.capitalize()} < Formula
  include Language::Python::Shebang

  # The current version of {PROJECT_NAME}
  desc "Manage .env secrets via system keychain with cloud store plugins"
  homepage "https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}"
  url "https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/releases/download/v{VERSION}/{PROJECT_NAME}-{VERSION}-macos-arm64.zip"
  sha256 "{arm64_sha256 or 'CHANGE_ME'}"
  license "AGPL-3.0-or-later"

  # Dependencies
  depends_on "python@3.12"

  # Bottles for different architectures
  bottle do
    root_url "https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/releases/download/v{VERSION}"
    sha256 cellar: :any_skip_relocation, arm64_sonoma: "{arm64_sha256 or 'CHANGE_ME'}"
    sha256 cellar: :any_skip_relocation, arm64_ventura: "{arm64_sha256 or 'CHANGE_ME'}"
    sha256 cellar: :any_skip_relocation, arm64_monterey: "{arm64_sha256 or 'CHANGE_ME'}"
    sha256 cellar: :any_skip_relocation, sonoma: "{x86_64_sha256 or 'CHANGE_ME'}"
    sha256 cellar: :any_skip_relocation, ventura: "{x86_64_sha256 or 'CHANGE_ME'}"
    sha256 cellar: :any_skip_relocation, monterey: "{x86_64_sha256 or 'CHANGE_ME'}"
  end

  def install
    # Install the binary
    bin.install "{PROJECT_NAME}" => "{PROJECT_NAME}"

    # Make sure it's executable
    chmod 0755, bin/"{PROJECT_NAME}"

    # Install completion if available
    if File.exist?("share/bash-completion/completions/{PROJECT_NAME}")
      bash_completion.install "share/bash-completion/completions/{PROJECT_NAME}"
    end
    if File.exist?("share/zsh/site-functions/_{PROJECT_NAME}")
      zsh_completion.install "share/zsh/site-functions/_{PROJECT_NAME}"
    end
  end

  test do
    # Test version command
    system bin/"{PROJECT_NAME}", "--version"
    # Test help command
    system bin/"{PROJECT_NAME}", "--help"
  end
end
'''

    return formula


def generate_formula_simple() -> str:
    """Generate a simpler Homebrew formula without bottle support."""
    formula = f'''# Copyright (c) 2026 Ramin Firoozye
# SPDX-License-Identifier: AGPL-3.0-or-later

class {PROJECT_NAME.capitalize()} < Formula
  desc "Manage .env secrets via system keychain with cloud store plugins"
  homepage "https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}"
  url "https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/releases/download/v{VERSION}/{PROJECT_NAME}-{VERSION}-macos-arm64.zip"
  sha256 "CHANGE_ME"
  license "AGPL-3.0-or-later"

  def install
    # Extract and install the binary
    prefix.install "bin/{PROJECT_NAME}"
    bin.install_symlink prefix/"bin/{PROJECT_NAME}" => "{PROJECT_NAME}"
  end

  test do
    system bin/"{PROJECT_NAME}", "--version"
  end
end
'''


def write_formula(output_path: Path) -> None:
    """Write the formula to a file."""
    formula = generate_formula()
    output_path.write_text(formula)
    print(f"Formula written to: {output_path}")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Generate Homebrew formula")
    parser.add_argument(
        "--output",
        "-o",
        default=None,
        help="Output file path (default: stdout)",
    )
    parser.add_argument(
        "--simple",
        action="store_true",
        default=False,
        help="Generate simple formula without bottle support",
    )

    args = parser.parse_args()

    if args.simple:
        formula = generate_formula_simple()
    else:
        formula = generate_formula()

    if args.output:
        output_path = Path(args.output)
        output_path.write_text(formula)
        print(f"Formula written to: {output_path}")
    else:
        print(formula)


if __name__ == "__main__":
    main()