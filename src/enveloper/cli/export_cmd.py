"""``enveloper export`` and ``enveloper unexport`` commands."""

from __future__ import annotations

import json
import sys

import click
from rich.console import Console

from enveloper.cli import (
    HAS_YAML,
    _get_keychain,
    _get_store,
    cli,
    common_options,
    console,
    key_to_export_name,
    KeychainStore,
    SecretStore,
)
from pathlib import Path

if HAS_YAML:
    import yaml


# ---------------------------------------------------------------------------
# export
# ---------------------------------------------------------------------------

@cli.command("export")
@click.option(
    "--format", "fmt",
    type=click.Choice(["dotenv", "unix", "win", "json", "yaml"]),
    default="dotenv",
    help="Output format: dotenv (default, KEY=value), unix (export KEY=value), win (PowerShell), json, yaml.",
)
@click.option(
    "--output", "-o",
    type=click.Path(exists=False),
    default=None,
    help="Output file path (default: stdout).",
)
@common_options
def export(ctx: click.Context, fmt: str, output: str | None) -> None:
    """Export secrets from the current service to stdout or file.

    Default format is dotenv (KEY=value, no "export") so output can recreate a
    local .env file and works on Windows. Use --format unix for shell sourcing:
    eval "$(enveloper export -d aws --format unix)". Use --format win for
    PowerShell: enveloper export -d aws --format win | Invoke-Expression (or iex).
    """
    project = ctx.obj["project"]
    domain = ctx.obj["domain"]
    service = ctx.obj["service"]

    store: SecretStore
    if service == "local" and domain is None:
        global_store = KeychainStore(project=project)
        domains = global_store.list_domains() or ["_default_"]
        pairs = {}
        for d in domains:
            store = _get_keychain(project, d)
            for key in store.list_keys():
                val = store.get(key)
                if val is not None:
                    pairs[key] = val
    else:
        store = _get_store(ctx)
        pairs = {}
        use_export_name = service not in ("local", "file")
        for key in store.list_keys():
            val = store.get(key)
            if val is not None:
                out_key = key_to_export_name(store, key) if use_export_name else key
                pairs[out_key] = val

    if output:
        path = Path(output)
        with path.open("w") as f:
            if fmt == "json":
                f.write(json.dumps(pairs, indent=2))
                f.write("\n")
            elif fmt == "yaml":
                if not HAS_YAML:
                    console.print("[red]PyYAML is not installed. Install with: pip install pyyaml[/red]")
                    return
                yaml.dump(pairs, f, default_flow_style=False, sort_keys=True)
            else:
                for line in _format_export_lines(pairs, fmt):
                    f.write(line + "\n")
        console.print(f"[green]Exported {len(pairs)} secret(s) to {output}[/green]")
    else:
        out = Console(file=sys.stdout, highlight=False)
        if fmt == "json":
            out.print(json.dumps(pairs, indent=2))
        elif fmt == "yaml":
            if not HAS_YAML:
                console.print("[red]PyYAML is not installed. Install with: pip install pyyaml[/red]")
                return
            yaml.dump(pairs, sys.stdout, default_flow_style=False, sort_keys=True)
        else:
            for line in _format_export_lines(pairs, fmt):
                out.print(line)


def _shell_escape(value: str) -> str:
    """Escape for Unix sh: single-quote wrapped, internal ' -> '\\''."""
    if not value or any(c in value for c in " \t'\"\\$`!#&|;(){}"):
        return "'" + value.replace("'", "'\\''") + "'"
    return value


def _powershell_escape(value: str) -> str:
    """Escape for PowerShell single-quoted string: ' -> ''."""
    return value.replace("'", "''")


def _format_export_lines(pairs: dict[str, str], fmt: str) -> list[str]:
    lines: list[str] = []
    for key, value in sorted(pairs.items()):
        if fmt == "dotenv":
            lines.append(f"{key}={value}")
        elif fmt == "unix":
            lines.append(f"export {key}={_shell_escape(value)}")
        elif fmt == "win":
            lines.append(f"$env:{key} = '{_powershell_escape(value)}'")
        else:
            lines.append(f"{key}={value}")
    return lines


# ---------------------------------------------------------------------------
# unexport
# ---------------------------------------------------------------------------

@cli.command("unexport")
@click.option(
    "--format", "fmt",
    type=click.Choice(["unix", "win"]),
    default="unix",
    help="Output format. Default: unix (unset KEY). Use win for PowerShell (Remove-Item Env:KEY).",
)
@common_options
def unexport(ctx: click.Context, fmt: str) -> None:
    """Output shell unset commands for all variables that export would set.

    Use with eval to clear env vars loaded by export. Unix: eval "$(enveloper export -d {domain} --format unix)"
    then eval "$(enveloper -d {domain} unexport)". Win: pipe export to Invoke-Expression, then
    enveloper unexport --format win | Invoke-Expression (or iex).
    """
    project = ctx.obj["project"]
    domain = ctx.obj["domain"]
    service = ctx.obj["service"]

    keys_out: list[str] = []
    store: SecretStore
    if service == "local" and domain is None:
        global_store = KeychainStore(project=project)
        domains = global_store.list_domains() or ["_default_"]
        for d in domains:
            store = _get_keychain(project, d)
            for key in store.list_keys():
                keys_out.append(key)
    else:
        store = _get_store(ctx)
        use_export_name = service not in ("local", "file")
        for key in store.list_keys():
            out_key = key_to_export_name(store, key) if use_export_name else key
            keys_out.append(out_key)

    out = Console(file=sys.stdout, highlight=False)
    for key in sorted(set(keys_out)):
        if fmt == "win":
            out.print(f"Remove-Item Env:{key} -ErrorAction SilentlyContinue")
        else:
            out.print(f"unset {key}")
