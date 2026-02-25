"""Enveloper CLI -- manage .env secrets via system keychain + cloud stores."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from enveloper import __version__
from enveloper.config import load_config
from enveloper.env_file import parse_env_file
from enveloper.stores import get_store_class
from enveloper.stores.keychain import KeychainStore

console = Console(stderr=True)


def _get_keychain(project: str, domain: str | None) -> KeychainStore:
    return KeychainStore(project=project, domain=domain)


@click.group()
@click.option("--project", "-p", default=None, help="Project namespace (default: from config).")
@click.option("--domain", "-d", default=None, help="Domain / subsystem scope.")
@click.option("--env", "-e", "env_name", default=None, help="Environment name (resolves {env}).")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output.")
@click.version_option(__version__)
@click.pass_context
def cli(
    ctx: click.Context,
    project: str | None,
    domain: str | None,
    env_name: str | None,
    verbose: bool,
) -> None:
    """Manage .env secrets via system keychain with cloud store plugins."""
    cfg = load_config()
    ctx.ensure_object(dict)
    ctx.obj["config"] = cfg
    ctx.obj["project"] = project or cfg.project
    ctx.obj["domain"] = domain
    ctx.obj["env_name"] = env_name
    ctx.obj["verbose"] = verbose


# ---------------------------------------------------------------------------
# import
# ---------------------------------------------------------------------------

@cli.command("import")
@click.argument("file", required=False, type=click.Path(exists=False))
@click.pass_context
def import_env(ctx: click.Context, file: str | None) -> None:
    """Import a .env file into the local keychain."""
    cfg = ctx.obj["config"]
    domain = ctx.obj["domain"]

    if file is None and domain and domain in cfg.domains:
        file = cfg.domains[domain].env_file
    if file is None:
        raise click.UsageError("Provide a file path or use --domain with a configured domain.")

    path = Path(file)
    if not path.is_file():
        raise click.BadParameter(f"File not found: {file}", param_hint="FILE")

    pairs = parse_env_file(path)
    if not pairs:
        console.print(f"[yellow]No variables found in {file}[/yellow]")
        return

    store = _get_keychain(ctx.obj["project"], domain)
    for key, value in pairs.items():
        store.set_with_domain_tracking(key, value)

    console.print(
        f"[green]Imported {len(pairs)} variable(s) from {file}"
        + (f" into domain '{domain}'" if domain else "")
        + "[/green]"
    )


# ---------------------------------------------------------------------------
# export
# ---------------------------------------------------------------------------

@cli.command()
@click.option(
    "--format", "fmt",
    type=click.Choice(["env", "dotenv", "json"]),
    default="env",
    help="Output format.",
)
@click.pass_context
def export(ctx: click.Context, fmt: str) -> None:
    """Export secrets from keychain to stdout.

    Use with eval: eval "$(enveloper export -d aws)"
    """
    project = ctx.obj["project"]
    domain = ctx.obj["domain"]

    if domain:
        domains = [domain]
    else:
        global_store = KeychainStore(project=project)
        domains = global_store.list_domains() or [None]  # type: ignore[list-item]

    pairs: dict[str, str] = {}
    for d in domains:
        store = _get_keychain(project, d)
        for key in store.list_keys():
            val = store.get(key)
            if val is not None:
                pairs[key] = val

    out = Console(file=sys.stdout, highlight=False)
    if fmt == "json":
        out.print(json.dumps(pairs, indent=2))
    else:
        for key, value in sorted(pairs.items()):
            if fmt == "env":
                out.print(f"export {key}={_shell_escape(value)}")
            else:
                out.print(f"{key}={value}")


def _shell_escape(value: str) -> str:
    if not value or any(c in value for c in " \t'\"\\$`!#&|;(){}"):
        return "'" + value.replace("'", "'\\''") + "'"
    return value


# ---------------------------------------------------------------------------
# get / set / rm
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("key")
@click.pass_context
def get(ctx: click.Context, key: str) -> None:
    """Get a single secret value."""
    store = _get_keychain(ctx.obj["project"], ctx.obj["domain"])
    value = store.get(key)
    if value is None:
        raise click.ClickException(f"Key '{key}' not found.")
    click.echo(value)


@cli.command("set")
@click.argument("key")
@click.argument("value")
@click.pass_context
def set_key(ctx: click.Context, key: str, value: str) -> None:
    """Set a single secret."""
    store = _get_keychain(ctx.obj["project"], ctx.obj["domain"])
    store.set_with_domain_tracking(key, value)
    console.print(f"[green]Set {key}[/green]")


@cli.command()
@click.argument("key")
@click.pass_context
def rm(ctx: click.Context, key: str) -> None:
    """Remove a single secret."""
    store = _get_keychain(ctx.obj["project"], ctx.obj["domain"])
    store.delete(key)
    console.print(f"[green]Removed {key}[/green]")


# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------

@cli.command("list")
@click.pass_context
def list_keys(ctx: click.Context) -> None:
    """List stored secret key names."""
    project = ctx.obj["project"]
    domain = ctx.obj["domain"]

    if domain:
        domains_to_show = [domain]
    else:
        global_store = KeychainStore(project=project)
        domains_to_show = global_store.list_domains() or []

    if not domains_to_show:
        console.print("[yellow]No secrets stored.[/yellow]")
        return

    table = Table(title=f"Secrets for project '{project}'")
    table.add_column("Domain", style="cyan")
    table.add_column("Key", style="white")
    table.add_column("Value (masked)", style="dim")

    for d in sorted(domains_to_show):
        store = _get_keychain(project, d)
        keys = store.list_keys()
        for key in sorted(keys):
            val = store.get(key)
            masked = _mask(val) if val else "(empty)"
            table.add_row(d, key, masked)

    console.print(table)


def _mask(value: str) -> str:
    if len(value) <= 6:
        return "****"
    return value[:3] + "****" + value[-3:]


# ---------------------------------------------------------------------------
# clear
# ---------------------------------------------------------------------------

@cli.command()
@click.confirmation_option(prompt="Are you sure you want to clear all secrets?")
@click.pass_context
def clear(ctx: click.Context) -> None:
    """Clear all secrets for the current project/domain."""
    project = ctx.obj["project"]
    domain = ctx.obj["domain"]

    if domain:
        store = _get_keychain(project, domain)
        store.clear()
        console.print(f"[green]Cleared all secrets in domain '{domain}'[/green]")
    else:
        global_store = KeychainStore(project=project)
        for d in global_store.list_domains():
            _get_keychain(project, d).clear()
        try:
            import keyring
            keyring.delete_password(f"enveloper:{project}", "__domains__")
        except Exception:
            pass
        console.print(f"[green]Cleared all secrets for project '{project}'[/green]")


# ---------------------------------------------------------------------------
# push / pull
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("store_name")
@click.option("--prefix", default=None, help="Key prefix for the target store.")
@click.option("--profile", default=None, help="AWS profile (aws-ssm store).")
@click.option("--region", default=None, help="AWS region (aws-ssm store).")
@click.option("--repo", default=None, help="GitHub repo owner/name (github store).")
@click.pass_context
def push(
    ctx: click.Context,
    store_name: str,
    prefix: str | None,
    profile: str | None,
    region: str | None,
    repo: str | None,
) -> None:
    """Push keychain secrets to a cloud store."""
    project = ctx.obj["project"]
    domain = ctx.obj["domain"]
    cfg = ctx.obj["config"]
    env_name = ctx.obj["env_name"]

    kc = _get_keychain(project, domain)
    keys = kc.list_keys()
    if not keys:
        console.print("[yellow]No secrets to push.[/yellow]")
        return

    target = _make_cloud_store(
        store_name, cfg, domain, env_name,
        prefix=prefix, profile=profile, region=region, repo=repo,
    )

    count = 0
    for key in keys:
        val = kc.get(key)
        if val is not None:
            target.set(key, val)
            count += 1
            if ctx.obj["verbose"]:
                console.print(f"  {key}")

    console.print(f"[green]Pushed {count} secret(s) to {store_name}[/green]")


@cli.command()
@click.argument("store_name")
@click.option("--prefix", default=None, help="Key prefix on the source store.")
@click.option("--profile", default=None, help="AWS profile (aws-ssm store).")
@click.option("--region", default=None, help="AWS region (aws-ssm store).")
@click.pass_context
def pull(
    ctx: click.Context,
    store_name: str,
    prefix: str | None,
    profile: str | None,
    region: str | None,
) -> None:
    """Pull secrets from a cloud store into the local keychain."""
    project = ctx.obj["project"]
    domain = ctx.obj["domain"]
    cfg = ctx.obj["config"]
    env_name = ctx.obj["env_name"]

    source = _make_cloud_store(
        store_name, cfg, domain, env_name,
        prefix=prefix, profile=profile, region=region,
    )

    keys = source.list_keys()
    if not keys:
        console.print("[yellow]No secrets found in remote store.[/yellow]")
        return

    kc = _get_keychain(project, domain)
    count = 0
    for key in keys:
        val = source.get(key)
        if val is not None:
            kc.set_with_domain_tracking(key, val)
            count += 1
            if ctx.obj["verbose"]:
                console.print(f"  {key}")

    console.print(f"[green]Pulled {count} secret(s) from {store_name}[/green]")


def _make_cloud_store(
    store_name: str,
    cfg: object,
    domain: str | None,
    env_name: str | None,
    *,
    prefix: str | None = None,
    profile: str | None = None,
    region: str | None = None,
    repo: str | None = None,
) -> object:
    """Instantiate a cloud store with resolved options."""
    from enveloper.config import EnveloperConfig

    assert isinstance(cfg, EnveloperConfig)
    store_cls = get_store_class(store_name)

    if store_name == "aws-ssm":
        resolved_prefix = prefix
        if resolved_prefix is None and domain:
            resolved_prefix = cfg.resolve_ssm_prefix(domain, env_name)
        if resolved_prefix is None:
            resolved_prefix = "/enveloper/"
        return store_cls(
            prefix=resolved_prefix,
            profile=profile or cfg.aws_profile,
            region=region or cfg.aws_region,
        )
    elif store_name == "github":
        gh_prefix = prefix if prefix is not None else cfg.github_prefix
        return store_cls(prefix=gh_prefix, repo=repo)
    else:
        return store_cls()


# ---------------------------------------------------------------------------
# stores
# ---------------------------------------------------------------------------

@cli.command()
def stores() -> None:
    """List available store plugins."""
    table = Table(title="Available Stores")
    table.add_column("Name", style="cyan")
    table.add_column("Module", style="dim")

    from importlib.metadata import entry_points as _eps

    for ep in sorted(_eps(group="enveloper.stores"), key=lambda e: e.name):
        table.add_row(ep.name, ep.value)

    console.print(table)


# ---------------------------------------------------------------------------
# generate
# ---------------------------------------------------------------------------

@cli.group()
def generate() -> None:
    """Generate configuration snippets."""


@generate.command("codebuild-env")
@click.option("--prefix", default=None, help="SSM prefix (e.g. /stillup/test/).")
@click.pass_context
def gen_codebuild(ctx: click.Context, prefix: str | None) -> None:
    """Generate AWS CodeBuild buildspec parameter-store YAML."""
    project = ctx.obj["project"]
    domain = ctx.obj["domain"]
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
        resolved_prefix = "/enveloper/"
    if not resolved_prefix.endswith("/"):
        resolved_prefix += "/"

    out = Console(file=sys.stdout, highlight=False)
    out.print("env:")
    out.print("  parameter-store:")
    for key in sorted(keys):
        out.print(f"    {key}: {resolved_prefix}{key}")
