#!/usr/bin/env python3
# Copyright (c) 2026 Ramin Firoozye
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Code signing script for macOS and Windows binaries."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import CERTS_DIR, DIST_DIR, ICONS_DIR, PROJECT_NAME, VERSION


def sign_macos_binary(binary_path: Path, identity: str | None = None) -> bool:
    """Sign a macOS binary using codesign."""
    if identity is None:
        identity = os.environ.get("MAC_CERT_IDENTITY", "Developer ID Application")

    print(f"Signing macOS binary: {binary_path}")
    print(f"Using identity: {identity}")

    # Check if certificate exists
    cert_path = CERTS_DIR / "mac.p12"
    if not cert_path.exists():
        print(f"Warning: Certificate not found at {cert_path}")
        print("Skipping signing. Place certificate at: binary/certs/mac.p12")
        return False

    # Check if password is available
    password_file = CERTS_DIR / "mac-cert-password.txt"
    if not password_file.exists():
        print(f"Warning: Password file not found at {password_file}")
        print("Skipping signing. Place password at: binary/certs/mac-cert-password.txt")
        return False

    password = password_file.read_text().strip()

    # Import certificate into keychain
    print("Importing certificate into keychain...")
    subprocess.run(
        [
            "security",
            "import",
            str(cert_path),
            "-k",
            "login.keychain-db",
            "-P",
            password,
            "-T",
            "/usr/bin/codesign",
        ],
        check=True,
    )

    # Sign the binary
    print("Signing binary...")
    result = subprocess.run(
        [
            "codesign",
            "--force",
            "--deep",
            "--sign",
            identity,
            str(binary_path),
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"Signing failed: {result.stderr}")
        return False

    print("Verification:")
    subprocess.run(["codesign", "--verify", "--deep", "--strict", str(binary_path)])

    return True


def sign_macos_pkg(pkg_path: Path, identity: str | None = None) -> bool:
    """Sign a macOS pkg installer."""
    if identity is None:
        identity = os.environ.get("MAC_CERT_IDENTITY", "Developer ID Installer")

    print(f"Signing macOS pkg: {pkg_path}")
    print(f"Using identity: {identity}")

    # Check if certificate exists
    cert_path = CERTS_DIR / "mac.p12"
    if not cert_path.exists():
        print(f"Warning: Certificate not found at {cert_path}")
        return False

    # Check if password is available
    password_file = CERTS_DIR / "mac-cert-password.txt"
    if not password_file.exists():
        print(f"Warning: Password file not found at {password_file}")
        return False

    password = password_file.read_text().strip()

    # Import certificate into keychain
    print("Importing certificate into keychain...")
    subprocess.run(
        [
            "security",
            "import",
            str(cert_path),
            "-k",
            "login.keychain-db",
            "-P",
            password,
            "-T",
            "/usr/bin/productsign",
        ],
        check=True,
    )

    # Sign the pkg
    print("Signing pkg...")
    signed_path = pkg_path.with_suffix(".signed.pkg")
    result = subprocess.run(
        [
            "productsign",
            "--sign",
            identity,
            str(pkg_path),
            str(signed_path),
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"Signing failed: {result.stderr}")
        return False

    # Replace original with signed version
    signed_path.rename(pkg_path)
    print(f"Signed pkg: {pkg_path}")

    return True


def sign_windows_binary(exe_path: Path, cert_path: Path | None = None) -> bool:
    """Sign a Windows binary using signtool."""
    # Check if signtool is available
    signtool = None
    possible_paths = [
        # Visual Studio
        Path(r"C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\amd64\signtool.exe"),
        Path(r"C:\Program Files (x86)\Windows Kits\10\bin\x64\signtool.exe"),
        Path(r"C:\Program Files (x86)\Windows Kits\10\bin\10.0.19041.0\x64\signtool.exe"),
    ]

    for p in possible_paths:
        if p.exists():
            signtool = p
            break

    if signtool is None:
        print("signtool not found. Please install Windows SDK or Visual Studio.")
        return False

    # Check if certificate exists
    if cert_path is None:
        cert_path = CERTS_DIR / "win.pfx"
    if not cert_path.exists():
        print(f"Warning: Certificate not found at {cert_path}")
        return False

    # Check if password is available
    password_file = CERTS_DIR / "win-cert-password.txt"
    if not password_file.exists():
        print(f"Warning: Password file not found at {password_file}")
        return False

    password = password_file.read_text().strip()

    print(f"Signing Windows binary: {exe_path}")

    # Sign the binary
    result = subprocess.run(
        [
            str(signtool),
            "sign",
            "/f",
            str(cert_path),
            "/p",
            password,
            "/t",
            "http://timestamp.digicert.com",
            "/fd",
            "sha256",
            str(exe_path),
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"Signing failed: {result.stderr}")
        return False

    print(f"Signed binary: {exe_path}")
    return True


def sign_all() -> bool:
    """Sign all built binaries."""
    all_signed = True

    # Sign macOS binaries
    print("\n=== Signing macOS Binaries ===")
    for arch in ["x86_64", "arm64"]:
        zip_path = DIST_DIR / f"{PROJECT_NAME}-{VERSION}-macos-{arch}.zip"
        if zip_path.exists():
            # Extract to sign
            extract_dir = DIST_DIR / "sign_extract"
            extract_dir.mkdir(exist_ok=True)
            subprocess.run(
                ["unzip", "-o", str(zip_path), "-d", str(extract_dir)],
                check=True,
            )
            binary_path = extract_dir / PROJECT_NAME
            if binary_path.exists():
                if not sign_macos_binary(binary_path):
                    all_signed = False
                # Re-zip
                subprocess.run(
                    ["zip", "-r", str(zip_path), PROJECT_NAME],
                    cwd=extract_dir,
                    check=True,
                )
            shutil.rmtree(extract_dir)

    # Sign Windows binaries
    print("\n=== Signing Windows Binaries ===")
    for arch in ["x86_64", "arm64"]:
        dir_path = DIST_DIR / f"{PROJECT_NAME}-{VERSION}-windows-{arch}"
        if dir_path.exists():
            exe_path = dir_path / f"{PROJECT_NAME}.exe"
            if exe_path.exists():
                if not sign_windows_binary(exe_path):
                    all_signed = False

    return all_signed


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Sign enveloper binaries")
    parser.add_argument(
        "--binary",
        "-b",
        default=None,
        help="Specific binary to sign",
    )
    parser.add_argument(
        "--platform",
        "-p",
        choices=["mac", "win"],
        default=None,
        help="Platform to sign (default: all)",
    )
    parser.add_argument(
        "--identity",
        "-i",
        default=None,
        help="Certificate identity for macOS signing",
    )
    parser.add_argument(
        "--cert",
        "-c",
        default=None,
        help="Certificate path for Windows signing",
    )

    args = parser.parse_args()

    if args.binary:
        binary_path = Path(args.binary)
        if not binary_path.exists():
            print(f"Binary not found: {binary_path}")
            sys.exit(1)

        if args.platform == "mac":
            if sign_macos_binary(binary_path, args.identity):
                print("\nSigning passed!")
                sys.exit(0)
            else:
                print("\nSigning failed!")
                sys.exit(1)
        elif args.platform == "win":
            if sign_windows_binary(binary_path, args.cert):
                print("\nSigning passed!")
                sys.exit(0)
            else:
                print("\nSigning failed!")
                sys.exit(1)

    if sign_all():
        print("\n=== All binaries signed! ===")
        sys.exit(0)
    else:
        print("\n=== Some binaries not signed! ===")
        sys.exit(1)


if __name__ == "__main__":
    main()