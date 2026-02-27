# Copyright (c) 2026 Ramin Firoozye
# SPDX-License-Identifier: AGPL-3.0-or-later

"""``enveloper clear`` command."""

from __future__ import annotations

import click

from enveloper.cli import _get_keychain, _get_store, cli, common_options, console, KeychainStore


@cli.command()
@click.option(
    "--quiet", "-q",
    is_flag=True,
    help="Skip confirmation prompts (for automation).",
)
@common_options
def clear(ctx: click.Context, quiet: bool) -> None:
    """Clear all secrets for the current service (local keychain, file, or cloud store).
    Without -d, local keychain clears all domains (same scope as list)."""
    service = ctx.obj["service"]

    if not quiet:
        if not click.confirm("Are you sure you want to clear all secrets?"):
            raise click.Abort()

    if service == "local" and ctx.obj["domain"] is None:
        project = ctx.obj["project"]
        global_store = KeychainStore(project=project)
        domains_to_clear = global_store.list_domains() or ["_default_"]
        for d in domains_to_clear:
            store = _get_keychain(project, d)
            store.clear()
        console.print(f"[green]Cleared all secrets for service 'local' (all domains)[/green]")
    else:
        store = _get_store(ctx)
        store.clear()
        if service == "local":
            domain = ctx.obj["domain_resolved"]
            console.print(f"[green]Cleared all secrets for service 'local' (domain '{domain}')[/green]")
        else:
            console.print(f"[green]Cleared all secrets for service '{service}'[/green]")
