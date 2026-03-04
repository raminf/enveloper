# Copyright (c) 2026 Ramin Firoozye
# SPDX-License-Identifier: AGPL-3.0-or-later

"""``enveloper clear`` command."""

from __future__ import annotations

import click

from enveloper.cli import KeychainStore, _get_broad_store, _get_keychain, _get_store, cli, common_options, console


def _confirm_clear_scope(domain: str, project: str, service: str) -> bool:
    """Print a short, colored scope line and confirm. Returns True to proceed."""
    if service == "local":
        console.print(
            "Clear  [dim]domain[/] [cyan]{domain}[/]  [dim]·[/]  [dim]project[/] [yellow]{project}[/]?"
            .format(domain=domain, project=project)
        )
    else:
        console.print(
            "Clear  [dim]domain[/] [cyan]{domain}[/]  [dim]·[/]  [dim]project[/] [yellow]{project}[/]  "
            "[dim]·[/]  [dim]service[/] [magenta]{service}[/]?".format(
                domain=domain, project=project, service=service
            )
        )
    return click.confirm("Proceed?", default=False)


def _confirm_clear_all(service: str) -> bool:
    """Print short, colored message and confirm. Returns True to proceed."""
    if service == "local":
        console.print("[bold]Clear ALL secrets[/] (every domain & project, local keychain).")
    else:
        console.print(
            "[bold]Clear ALL secrets[/] (every domain & project)  "
            "[dim]·[/]  [dim]service[/] [magenta]{0}[/].".format(service)
        )
    if not click.confirm("Proceed?", default=False):
        return False
    console.print("[dim]This cannot be undone.[/]")
    return click.confirm("Really sure?", default=False)


@cli.command()
@click.option(
    "--quiet", "-q",
    is_flag=True,
    help="Skip confirmation prompts (for automation).",
)
@click.option(
    "--all", "clear_all",
    is_flag=True,
    help="Clear secrets across ALL projects and domains.",
)
@common_options
def clear(ctx: click.Context, quiet: bool, clear_all: bool) -> None:
    """Clear secrets for a specific domain/project, or everything with --all."""
    service = ctx.obj["service"]
    domain = ctx.obj.get("domain_resolved", "_default_")
    project = ctx.obj.get("project", "_default_")

    if clear_all:
        if not quiet and not _confirm_clear_all(service):
            raise click.Abort()

        if service == "local":
            for proj in KeychainStore.list_all_projects() or ["_default_"]:
                proj_store = KeychainStore(project=proj)
                for d in proj_store.list_domains() or ["_default_"]:
                    _get_keychain(proj, d).clear()
                KeychainStore.unregister_global_project(proj)
        else:
            store = _get_broad_store(ctx)
            if quiet:
                store.clear()
                store.clear_metadata()
            else:
                with console.status(f"Clearing all secrets on [bold]{service}[/bold]…", spinner="circle"):
                    store.clear()
                    store.clear_metadata()
        console.print(f"[green]Cleared ALL secrets for every project and domain ({service})[/green]")
        return

    if not quiet and not _confirm_clear_scope(domain, project, service):
        raise click.Abort()

    if service == "local":
        store = _get_keychain(project, domain)
        store.clear()
        if not KeychainStore(project=project).list_domains():
            KeychainStore.unregister_global_project(project)
    else:
        store_to_clear = _get_store(ctx)
        if quiet:
            store_to_clear.clear()
            store_to_clear.clear_metadata()
        else:
            with console.status(f"Clearing secrets on [bold]{service}[/bold]…", spinner="circle"):
                store_to_clear.clear()
                store_to_clear.clear_metadata()

    console.print(f"[green]Cleared secrets for domain '{domain}', project '{project}'[/green]")
