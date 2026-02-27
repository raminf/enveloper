# Copyright (c) 2026 Ramin Firoozye
# SPDX-License-Identifier: AGPL-3.0-or-later

"""``enveloper generate`` command group (codebuild-env, etc.)."""

from __future__ import annotations

import sys

import click
from rich.console import Console

from enveloper.cli import _get_keychain, cli, common_options, console


@cli.group()
def generate() -> None:
    """Generate configuration snippets."""


@generate.command("codebuild-env")
@click.option("--prefix", default=None, help="SSM prefix (e.g. /stillup/test/).")
@common_options
def gen_codebuild(ctx: click.Context, prefix: str | None) -> None:
    """Generate AWS CodeBuild buildspec parameter-store YAML."""
    project = ctx.obj["project"]
    domain = ctx.obj["domain_resolved"]
    cfg = ctx.obj["config"]
    env_name = ctx.obj["env_name"]

    kc = _get_keychain(project, domain)
    keys = kc.list_keys()
    if not keys:
        console.print("[yellow]No secrets to generate from.[/yellow]")
        return

    resolved_prefix = prefix
    if resolved_prefix is None and domain:
        resolved_prefix = cfg.resolve_ssm_prefix(domain, env_name)
    if resolved_prefix is None:
        resolved_prefix = "/envr/"
    if not resolved_prefix.endswith("/"):
        resolved_prefix += "/"

    out = Console(file=sys.stdout, highlight=False)
    out.print("env:")
    out.print("  parameter-store:")
    for key in sorted(keys):
        out.print(f"    {key}: {resolved_prefix}{key}")
