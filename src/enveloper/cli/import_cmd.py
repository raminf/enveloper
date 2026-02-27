# Copyright (c) 2026 Ramin Firoozye
# SPDX-License-Identifier: AGPL-3.0-or-later

"""``enveloper import`` -- import a file into the local keychain."""

from __future__ import annotations

import json
from pathlib import Path

import click

from enveloper.cli import (
    HAS_YAML,
    _get_store,
    cli,
    common_options,
    console,
    KeychainStore,
)
from enveloper.env_file import parse_env_file

if HAS_YAML:
    import yaml


@cli.command("import")
@click.argument("file", required=False, type=click.Path(exists=False))
@click.option(
    "--format", "fmt",
    type=click.Choice(["env", "json", "yaml"]),
    default="env",
    help="Input format (env, json, yaml). Default: env.",
)
@common_options
def import_env(ctx: click.Context, file: str | None, fmt: str) -> None:
    """Import a file into the local keychain.

    Supports .env, JSON, and YAML formats.

    For JSON/YAML, supports nested structure with domains and projects:
    {
        "domain_name": {
            "project_name": {
                "KEY": "value"
            }
        }
    }
    """
    cfg = ctx.obj["config"]
    domain = ctx.obj["domain"]

    if file is None and domain and domain in cfg.domains:
        file = cfg.domains[domain].env_file
    if file is None:
        raise click.UsageError("Provide a file path or use --domain with a configured domain.")

    path = Path(file)
    if not path.is_file():
        raise click.BadParameter(f"File not found: {file}", param_hint="FILE")

    if fmt == "env":
        pairs = parse_env_file(path)
    else:
        if fmt == "json":
            try:
                content = path.read_text()
                data = json.loads(content)
            except json.JSONDecodeError as e:
                raise click.ClickException(f"Invalid JSON file: {e}")
        else:
            if not HAS_YAML:
                raise click.ClickException(
                    "PyYAML is not installed. Install with: pip install pyyaml"
                )
            try:
                content = path.read_text()
                data = yaml.safe_load(content)
            except yaml.YAMLError as e:
                raise click.ClickException(f"Invalid YAML file: {e}")

        pairs = {}
        if isinstance(data, dict):
            has_domains = False
            has_projects = False

            for k, v in data.items():
                if isinstance(v, dict):
                    for pk, pv in v.items():
                        if isinstance(pv, dict):
                            has_projects = True
                        else:
                            has_domains = True
                        break
                    break

            if has_projects:
                for d_name, d_content in data.items():
                    if isinstance(d_content, dict):
                        for p_name, p_content in d_content.items():
                            if isinstance(p_content, dict):
                                for k, v in p_content.items():
                                    pairs[k] = str(v)
            elif has_domains:
                for d_name, d_content in data.items():
                    if isinstance(d_content, dict):
                        for k, v in d_content.items():
                            pairs[k] = str(v)
            else:
                for k, v in data.items():
                    pairs[k] = str(v)
        elif isinstance(data, list):
            raise click.ClickException(
                f"{fmt.upper()} file must contain an object/dictionary, not a list."
            )
        else:
            raise click.ClickException(
                f"{fmt.upper()} file must contain an object/dictionary."
            )

    if not pairs:
        console.print(f"[yellow]No variables found in {file}[/yellow]")
        return

    store = _get_store(ctx)
    for key, value in pairs.items():
        if isinstance(store, KeychainStore):
            store.set_with_domain_tracking(key, value)
        else:
            store.set(key, value)

    console.print(
        f"[green]Imported {len(pairs)} variable(s) from {file}[/green]"
    )
