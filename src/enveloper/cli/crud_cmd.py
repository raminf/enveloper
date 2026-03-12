# Copyright (c) 2026 Ramin Firoozye
# SPDX-License-Identifier: AGPL-3.0-or-later

"""``enveloper get``, ``enveloper set``, ``enveloper delete`` commands."""

from __future__ import annotations

import click

from enveloper.cli import _get_store, cli, common_options, console
from enveloper.security import SanitizationError, sanitize_secret_key, sanitize_secret_pair


@cli.command()
@click.argument("key")
@common_options
def get(ctx: click.Context, key: str) -> None:
    """Get a single secret value."""
    try:
        store = _get_store(ctx)
        value = store.get(sanitize_secret_key(key))
    except SanitizationError as e:
        raise click.ClickException(str(e))
    if value is None:
        raise click.ClickException(f"Key '{key}' not found.")
    click.echo(value)


@cli.command("set")
@click.argument("key")
@click.argument("value")
@common_options
def set_key(ctx: click.Context, key: str, value: str) -> None:
    """Set a single secret."""
    try:
        safe_key, safe_value = sanitize_secret_pair(key, value)
        store = _get_store(ctx)
        store.set_with_tracking(safe_key, safe_value)
    except SanitizationError as e:
        raise click.ClickException(str(e))
    console.print(f"[green]Set {key}[/green]")


@cli.command()
@click.argument("key")
@common_options
def delete(ctx: click.Context, key: str) -> None:
    """Remove a single secret."""
    try:
        store = _get_store(ctx)
        store.delete_with_tracking(sanitize_secret_key(key))
    except SanitizationError as e:
        raise click.ClickException(str(e))
    console.print(f"[green]Removed {key}[/green]")
