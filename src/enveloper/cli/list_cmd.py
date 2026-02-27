# Copyright (c) 2026 Ramin Firoozye
# SPDX-License-Identifier: AGPL-3.0-or-later

"""``enveloper list`` command."""

from __future__ import annotations

import click
from rich.table import Table

from enveloper.cli import (
    _get_keychain,
    _get_store,
    _mask,
    cli,
    common_options,
    console,
    key_to_export_name,
    KeychainStore,
    SecretStore,
)


@cli.command("list")
@common_options
def list_keys(ctx: click.Context) -> None:
    """List stored secret key names."""
    project = ctx.obj["project"]
    domain = ctx.obj["domain"]
    service = ctx.obj["service"]
    version = ctx.obj.get("version")
    store: SecretStore

    if service == "local" and domain is None:
        global_store = KeychainStore(project=project)
        domains_to_show = global_store.list_domains() or ["_default_"]
        if not domains_to_show:
            console.print("[yellow]No secrets stored.[/yellow]")
            return
        table = Table(title=f"Secrets for project '{project}'")
        table.add_column("Project", style="cyan")
        table.add_column("Domain", style="cyan")
        table.add_column("Version", style="cyan")
        table.add_column("Key", style="white")
        table.add_column("Value (masked)", style="dim")
        has_secrets = False
        for d in sorted(domains_to_show):
            store = _get_keychain(project, d)
            keys = store.list_keys()
            if not keys:
                table.add_row(project, d, "(empty)", "(empty)", "(empty)")
                has_secrets = True
                continue
            for key in sorted(keys):
                val = store.get(key)
                masked = _mask(val) if val else "(empty)"
                table.add_row(project, d, store._version, key, masked)
                has_secrets = True
        if not has_secrets:
            console.print("[yellow]No secrets stored.[/yellow]")
            return
        console.print(table)
    else:
        store = _get_store(ctx)
        keys = store.list_keys()
        keys_with_values = [(k, store.get(k)) for k in keys]
        keys_to_show = [(k, v) for k, v in keys_with_values if v is not None]
        title = f"Secrets ({service})"
        if service == "file":
            title = f"Secrets (file: {ctx.obj['path']})"
        table = Table(title=title)
        table.add_column("Key", style="white")
        table.add_column("Value (masked)", style="dim")
        if not keys_to_show:
            table.add_row("(empty)", "(empty)")
        else:
            for key, val in sorted(keys_to_show, key=lambda x: x[0]):
                display_key = key_to_export_name(store, key) if service not in ("local", "file") else key
                table.add_row(display_key, _mask(val))
        console.print(table)
