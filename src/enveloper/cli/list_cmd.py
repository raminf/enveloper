# Copyright (c) 2026 Ramin Firoozye
# SPDX-License-Identifier: AGPL-3.0-or-later

"""``enveloper list`` command."""

from __future__ import annotations

import click
from rich.panel import Panel
from rich.table import Table

from enveloper.cli import (
    KeychainStore,
    _get_keychain,
    _get_metadata_store,
    _get_store,
    _mask,
    cli,
    common_options,
    console,
    key_to_export_name,
)
from enveloper.store import SecretStore


@cli.group("list", invoke_without_command=True)
@common_options
@click.pass_context
def list_group(
    ctx: click.Context,
    project: str | None = None,
    domain: str | None = None,
    service: str | None = None,
    version: str | None = None,
) -> None:
    """List stored secrets by domain, project, or keys."""
    if ctx.invoked_subcommand is None:
        table = Table(
            title="List commands",
            show_header=True,
            header_style="bold cyan",
        )
        table.add_column("Command", style="cyan")
        table.add_column("Description", style="dim")
        table.add_row("list domain", "List all domains (and their projects) that have secrets.")
        table.add_row("list project", "List all projects that have secrets in a domain.")
        table.add_row("list keys", "List keys and values for a domain and project.")
        console.print(Panel(table, border_style="dim"))


@list_group.command("domain")
@common_options
def list_domains(ctx: click.Context) -> None:
    """List all domains that have secrets.

    For the local keychain, scans all registered projects and shows which
    domains exist in each.  For cloud stores, lists domains for the current
    project/prefix.
    """
    service = ctx.obj["service"]

    if service == "local":
        all_domains = KeychainStore.list_all_domains()
        if not all_domains:
            console.print("[yellow]No domains found.[/yellow]")
            return
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Project", style="white")
        table.add_column("Domain", style="cyan")
        for project in sorted(all_domains):
            for d in sorted(all_domains[project]):
                table.add_row(project, d)
        console.print(Panel(table, title="Domains (local keychain)", border_style="dim"))
    else:
        store = _get_metadata_store(ctx)
        with console.status(f"Listing domains from [bold]{service}[/bold]…", spinner="circle"):
            domains = store.list_domains()
        if not domains:
            console.print("[yellow]No domains found.[/yellow]")
            return
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Project", style="white")
        table.add_column("Domain", style="cyan")
        for d in sorted(domains):
            for p in sorted(store.list_projects(d)):
                table.add_row(p, d)
        console.print(Panel(table, title=f"Domains ({service})", border_style="dim"))


list_group.add_command(list_domains, "domains")


@list_group.command("project")
@common_options
def list_project_secrets(ctx: click.Context) -> None:
    """List all projects that have secrets in a domain.

    If --domain is omitted, uses _default_.  For the local keychain, scans
    all registered projects.  For cloud stores, lists projects via the
    store's own ``list_projects`` method.
    """
    service = ctx.obj["service"]
    domain = ctx.obj.get("domain_resolved") or "_default_"
    ctx.obj["domain_resolved"] = domain

    default_label = " (default)" if domain == "_default_" else ""

    if service == "local":
        projects = KeychainStore.list_projects_for_domain(domain)
        if not projects:
            console.print(f"[yellow]No projects found for domain '{domain}'.[/yellow]")
            return
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Project", style="cyan")
        for p in sorted(projects):
            table.add_row(p)
        console.print(Panel(
            table,
            title=f"Projects in domain '{domain}'{default_label}",
            border_style="dim",
        ))
    else:
        store = _get_metadata_store(ctx)
        with console.status(f"Listing projects from [bold]{service}[/bold]…", spinner="circle"):
            projects = store.list_projects(domain)
        if not projects:
            console.print(f"[yellow]No projects found for domain '{domain}'.[/yellow]")
            return
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Project", style="cyan")
        for p in sorted(projects):
            table.add_row(p)
        console.print(Panel(
            table,
            title=f"Projects in domain '{domain}'{default_label} ({service})",
            border_style="dim",
        ))


list_group.add_command(list_project_secrets, "projects")


@list_group.command("keys")
@common_options
def list_keys(ctx: click.Context) -> None:
    """List keys and values for a domain and project.

    If --domain or --project are omitted, uses _default_ for each (or the
    service provider's default namespace).
    """
    service = ctx.obj["service"]
    domain = ctx.obj.get("domain_resolved") or "_default_"
    project = ctx.obj.get("project") or "_default_"
    ctx.obj["domain_resolved"] = domain

    store: SecretStore
    if service == "local":
        store = _get_keychain(project, domain)
    else:
        store = _get_store(ctx)

    if service not in ("local", "file"):
        with console.status(f"Listing keys from [bold]{service}[/bold]…", spinner="circle"):
            keys = store.list_keys()
            keys_with_values = [(k, store.get(k)) for k in keys]
    else:
        keys = store.list_keys()
        keys_with_values = [(k, store.get(k)) for k in keys]
    keys_to_show = [(k, v) for k, v in keys_with_values if v is not None]

    title = f"Secrets for domain '{domain}', project '{project}'"
    if service not in ("local", "file"):
        title += f" ({service})"

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Key", style="white")
    table.add_column("Value (masked)", style="dim")

    if not keys_to_show:
        table.add_row("(empty)", "(empty)")
    else:
        for key, val in sorted(keys_to_show, key=lambda x: x[0]):
            display_key = key_to_export_name(store, key) if service not in ("local", "file") else key
            table.add_row(display_key, _mask(val))

    console.print(Panel(table, title=title, border_style="dim"))


list_group.add_command(list_keys, "key")
