"""``enveloper service`` and ``enveloper stores`` commands."""

from __future__ import annotations

import click
from rich.table import Table

from enveloper.cli import _doc_link, cli, common_options, console, get_service_entries


def _service_table_separator_row() -> tuple[str, str, str]:
    """Return a row of horizontal rules for visual separation in the service table."""
    return ("─" * 12, "─" * 36, "─" * 11)


@cli.command("service")
@common_options
def service_list(ctx: click.Context) -> None:
    """List all available service providers in a table (local, file, then cloud stores).

    Each store provides its short name, description, and documentation link
    via class attributes and get_service_rows().
    """
    table = Table(title="Service providers")
    table.add_column("Service", style="cyan")
    table.add_column("Description", style="white")
    table.add_column("Documentation", style="dim")
    prev_entry: str | None = None
    for entry_name, store_cls in get_service_entries():
        if prev_entry == "keychain":
            table.add_row(*_service_table_separator_row(), style="dim")
        elif prev_entry == "file":
            table.add_row(*_service_table_separator_row(), style="dim")
        for short_name, display_name, doc_url in store_cls.get_service_rows():
            doc_cell = _doc_link(doc_url) if doc_url else ""
            table.add_row(short_name, display_name, doc_cell)
        prev_entry = entry_name
    console.print(table)
    console.print("[yellow]Note: To open documentation links, you may need to Command-Click on them.[/yellow]")


@cli.command()
@common_options
def stores(ctx: click.Context) -> None:
    """List available store plugins."""
    table = Table(title="Available Stores")
    table.add_column("Name", style="cyan")
    table.add_column("Module", style="dim")

    from importlib.metadata import entry_points as _eps

    for ep in sorted(_eps(group="enveloper.stores"), key=lambda e: e.name):
        table.add_row(ep.name, ep.value)

    console.print(table)
