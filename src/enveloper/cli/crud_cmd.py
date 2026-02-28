# Copyright (c) 2026 Ramin Firoozye
# SPDX-License-Identifier: AGPL-3.0-or-later

"""``enveloper get``, ``enveloper set``, ``enveloper delete`` commands."""

from __future__ import annotations

import click

from enveloper.cli import KeychainStore, _get_store, cli, common_options, console


@cli.command()
@click.argument("key")
@common_options
def get(ctx: click.Context, key: str) -> None:
    """Get a single secret value."""
    store = _get_store(ctx)
    value = store.get(key)
    if value is None:
        raise click.ClickException(f"Key '{key}' not found.")
    click.echo(value)


@cli.command("set")
@click.argument("key")
@click.argument("value")
@common_options
def set_key(ctx: click.Context, key: str, value: str) -> None:
    """Set a single secret."""
    store = _get_store(ctx)
    if isinstance(store, KeychainStore):
        store.set_with_domain_tracking(key, value)
    else:
        store.set(key, value)
    console.print(f"[green]Set {key}[/green]")


@cli.command()
@click.argument("key")
@common_options
def delete(ctx: click.Context, key: str) -> None:
    """Remove a single secret."""
    store = _get_store(ctx)
    store.delete(key)
    console.print(f"[green]Removed {key}[/green]")
