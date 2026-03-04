# Copyright (c) 2026 Ramin Firoozye
# SPDX-License-Identifier: AGPL-3.0-or-later

"""``enveloper clear`` command."""

from __future__ import annotations

import click

from enveloper.cli import KeychainStore, _get_broad_store, _get_keychain, _get_store, cli, common_options, console


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
        if not quiet:
            svc_label = f" on service '{service}'" if service != "local" else ""
            if not click.confirm(f"This will delete ALL secrets across every project and domain{svc_label}. Are you sure?"):
                raise click.Abort()
            if not click.confirm("This cannot be undone. Are you REALLY sure?"):
                raise click.Abort()

        if service == "local":
            for proj in KeychainStore.list_all_projects() or ["_default_"]:
                proj_store = KeychainStore(project=proj)
                for d in proj_store.list_domains() or ["_default_"]:
                    _get_keychain(proj, d).clear()
                KeychainStore.unregister_global_project(proj)
        else:
            store = _get_broad_store(ctx)
            store.clear()
            store.clear_metadata()
        console.print(f"[green]Cleared ALL secrets for every project and domain ({service})[/green]")
        return

    if not quiet:
        prompt = f"Clear all secrets for domain '{domain}', project '{project}'"
        if service != "local":
            prompt += f", service '{service}'"
        prompt += "?"
        if not click.confirm(prompt):
            raise click.Abort()

    if service == "local":
        store = _get_keychain(project, domain)
        store.clear()
        if not KeychainStore(project=project).list_domains():
            KeychainStore.unregister_global_project(project)
    else:
        store_to_clear = _get_store(ctx)
        store_to_clear.clear()
        store_to_clear.clear_metadata()

    console.print(f"[green]Cleared secrets for domain '{domain}', project '{project}'[/green]")
