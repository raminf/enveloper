# Copyright (c) 2026 Ramin Firoozye
# SPDX-License-Identifier: AGPL-3.0-or-later

"""``enveloper init`` -- configure the OS keychain for frictionless access."""

from __future__ import annotations

from pathlib import Path

import click

from enveloper.cli import cli, common_options, console


@cli.command()
@common_options
def init(ctx: click.Context) -> None:
    """Configure the OS keychain for frictionless access.

    Platform-specific setup to minimize password prompts during builds.
    """
    import platform
    import shutil
    import subprocess

    system = platform.system()

    if system == "Darwin":
        console.print("[bold]macOS keychain setup[/bold]\n")

        kc_path = Path.home() / "Library" / "Keychains" / "login.keychain-db"
        if kc_path.exists():
            try:
                subprocess.run(
                    ["security", "set-keychain-settings", str(kc_path)],
                    check=True,
                    capture_output=True,
                )
                console.print("[green]  Login keychain auto-lock disabled.[/green]")
            except subprocess.CalledProcessError:
                console.print(
                    "[yellow]  Could not disable keychain auto-lock "
                    "(may require unlocked keychain).[/yellow]"
                )
        else:
            console.print("[dim]  Login keychain not found at default path.[/dim]")

        pam_sudo_local = Path("/etc/pam.d/sudo_local")
        tid_line = "auth       sufficient     pam_tid.so"
        if Path("/usr/lib/pam/pam_tid.so.2").exists() or Path(
            "/usr/lib/pam/pam_tid.so"
        ).exists():
            if pam_sudo_local.exists() and "pam_tid.so" in pam_sudo_local.read_text():
                console.print("[green]  Touch ID for sudo: already enabled.[/green]")
            else:
                console.print(
                    "\n  Touch ID can be used for sudo (useful for build commands)."
                )
                console.print(
                    f"  To enable, add this line to [bold]{pam_sudo_local}[/bold]:\n"
                )
                console.print(f"    {tid_line}\n")
                console.print(
                    "  Run: [dim]sudo sh -c 'echo \"auth       sufficient     "
                    "pam_tid.so\" > /etc/pam.d/sudo_local'[/dim]"
                )
        else:
            console.print("[dim]  Touch ID module not found (older macOS?).[/dim]")

        console.print(
            "\n[bold]Note:[/bold] On first keychain access, macOS shows an "
            '"allow this application" dialog.\n'
            "Click [bold]Always Allow[/bold] to prevent future prompts for "
            "this Python binary."
        )

    elif system == "Linux":
        console.print("[bold]Linux secret service setup[/bold]\n")

        has_dbus = shutil.which("dbus-send")
        if has_dbus:
            try:
                result = subprocess.run(
                    [
                        "dbus-send",
                        "--session",
                        "--print-reply",
                        "--dest=org.freedesktop.secrets",
                        "/org/freedesktop/secrets",
                        "org.freedesktop.DBus.Peer.Ping",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    console.print(
                        "[green]  Secret service daemon is running.[/green]"
                    )
                else:
                    console.print(
                        "[yellow]  Secret service daemon not responding.[/yellow]"
                    )
                    console.print(
                        "  Install gnome-keyring or kwallet and ensure it starts "
                        "at login."
                    )
            except (subprocess.TimeoutExpired, FileNotFoundError):
                console.print(
                    "[yellow]  Could not check secret service status.[/yellow]"
                )
        else:
            console.print(
                "[yellow]  dbus-send not found. "
                "Install dbus and a secret service (gnome-keyring or kwallet).[/yellow]"
            )

        console.print(
            "\n[bold]Note:[/bold] GNOME Keyring and KDE Wallet auto-unlock at "
            "login.\nNo repeated password prompts during builds."
        )

    elif system == "Windows":
        console.print("[bold]Windows credential setup[/bold]\n")
        console.print(
            "[green]  Windows Credential Locker is unlocked with your "
            "user session.[/green]\n"
            "  No additional setup needed. Secrets are accessible "
            "once you are logged in."
        )
        console.print(
            "\n[bold]Note:[/bold] If Windows Hello (fingerprint/face) is "
            "configured for login,\ncredentials are available after biometric "
            "unlock."
        )

    else:
        console.print(f"[yellow]Unknown platform: {system}[/yellow]")
        console.print(
            "Enveloper uses the 'keyring' library which supports "
            "most secret service backends."
        )

    console.print("\n[green]Init complete.[/green]")
