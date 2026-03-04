# Copyright (c) 2026 Ramin Firoozye
# SPDX-License-Identifier: AGPL-3.0-or-later

"""``enveloper rebuild`` -- rebuild the metadata registry from existing secrets."""

from __future__ import annotations

import click

from enveloper.cli import _get_broad_store, cli, common_options, console


@cli.command()
@common_options
def rebuild(ctx: click.Context) -> None:
    """Rebuild the domain/project metadata registry by scanning existing secrets.

    Use this if metadata keys were accidentally deleted or are out of sync.
    Works for all cloud services and local keychain.
    """
    service = ctx.obj.get("service", "local")

    if service == "local":
        console.print("[yellow]Local keychain registry is managed automatically; nothing to rebuild.[/yellow]")
        return

    store = _get_broad_store(ctx)
    result = store.rebuild_registry()

    if not result:
        console.print(f"[yellow]No enveloper secrets found for service '{service}'.[/yellow]")
        return

    total_projects = sum(len(ps) for ps in result.values())
    console.print(
        f"[green]Rebuilt metadata registry for service '{service}': "
        f"{len(result)} domain(s), {total_projects} project(s).[/green]"
    )
    for domain, projects in sorted(result.items()):
        console.print(f"  {domain}: {', '.join(projects)}")
