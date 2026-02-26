"""Enveloper CLI -- manage .env secrets via system keychain + cloud stores."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.style import Style
from rich.table import Table
from rich.text import Text

from enveloper import __version__
from enveloper.config import load_config
from enveloper.env_file import parse_env_file
from enveloper.resolve_store import get_store as resolve_get_store
from enveloper.resolve_store import make_cloud_store as resolve_make_cloud_store
from enveloper.store import SecretStore
from enveloper.stores import list_store_names
from enveloper.stores.keychain import KeychainStore
from enveloper.util import strip_domain_prefix

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

console = Console(stderr=True)

# Service provider metadata for `enveloper service` (description and doc links).
# "local" is expanded into three platform rows; each has two doc links: keyring (library) + platform (OS docs).
_KEYRING_URL = "https://github.com/jaraco/keyring"
_LOCAL_PLATFORMS: list[tuple[str, str, str]] = [
    (
        "local (macOS)",
        "macOS Keychain",
        "https://support.apple.com/guide/keychain-access/welcome/mac",
    ),
    (
        "local (Windows)",
        "Windows Credential Locker",
        "https://learn.microsoft.com/en-us/windows/win32/secauthn/credential-manager",
    ),
    (
        "local (Linux)",
        "Linux Secret Service",
        "https://specifications.freedesktop.org/secret-service/",
    ),
]
_SERVICE_PROVIDER_INFO: dict[str, tuple[str, str]] = {
    "file": (
        "Plain .env file",
        "https://github.com/motdotla/dotenv",
    ),
    "aws": (
        "AWS Systems Manager Parameter Store",
        "https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html",
    ),
    "github": (
        "GitHub Actions encrypted secrets",
        "https://docs.github.com/en/actions/security-guides/encrypted-secrets",
    ),
    "vault": (
        "HashiCorp Vault KV v2",
        "https://developer.hashicorp.com/vault/docs",
    ),
    "gcp": (
        "Google Cloud Secret Manager",
        "https://cloud.google.com/secret-manager/docs",
    ),
    "azure": (
        "Azure Key Vault",
        "https://learn.microsoft.com/en-us/azure/key-vault/",
    ),
    "aliyun": (
        "Alibaba Cloud KMS Secrets Manager",
        "https://www.alibabacloud.com/help/en/kms/key-management-service/getting-started/getting-started-with-secrets-manager",
    ),
}


def _doc_link(url: str, label: str = "Open") -> Text:
    """Return a Rich Text renderable with an OSC 8 hyperlink for terminal clickability."""
    return Text(label, style=Style(link=url))


def _local_doc_cell(keyring_url: str, platform_url: str) -> Text:
    """Two links for local rows: keyring (library) and docs (OS-specific)."""
    return (
        Text("keyring", style=Style(link=keyring_url))
        .append(" · ")
        .append("docs", style=Style(link=platform_url))
    )


def _get_keychain(project: str, domain: str | None) -> KeychainStore:
    return KeychainStore(project=project, domain=domain)


def _get_store(ctx: click.Context) -> SecretStore:
    """Return the current store for get/set/list/import/export (from --service and --path)."""
    service = ctx.obj.get("service", "local")
    project = ctx.obj["project"]
    domain = ctx.obj.get("domain_resolved", "default")
    cfg = ctx.obj["config"]
    env_name = ctx.obj["env_name"]
    path = ctx.obj.get("path", ".env")
    try:
        return resolve_get_store(
            service, project, domain, cfg,
            path=path, env_name=env_name,
        )
    except ValueError as e:
        raise click.UsageError(str(e))


@click.group()
@click.option("--project", "-p", default=None, help="Project namespace (default: from config or ENVELOPER_PROJECT env var).")
@click.option("--domain", "-d", default=None, help="Domain / subsystem scope (default: from ENVELOPER_DOMAIN env var).")
@click.option(
    "--service", "-s", default=None,
    help="Backend: local, file (.env), or cloud. Default: ENVELOPER_SERVICE or config, else local.",
)
@click.option("--path", default=None, help="Path to .env file when --service file (default: .env).")
@click.option("--env", "-e", "env_name", default=None, help="Environment name (resolves {env}).")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output.")
@click.version_option(__version__)
@click.pass_context
def cli(
    ctx: click.Context,
    project: str | None,
    domain: str | None,
    service: str | None,
    path: str | None,
    env_name: str | None,
    verbose: bool,
) -> None:
    """Manage .env secrets via system keychain with cloud store plugins."""
    import os

    cfg = load_config()
    ctx.ensure_object(dict)
    ctx.obj["config"] = cfg
    # Environment variables take precedence over CLI options
    ctx.obj["project"] = project or os.environ.get("ENVELOPER_PROJECT") or cfg.project
    ctx.obj["domain"] = domain or os.environ.get("ENVELOPER_DOMAIN")  # None if not set
    ctx.obj["domain_resolved"] = ctx.obj["domain"] or "default"
    ctx.obj["service"] = (
        service
        if service is not None
        else (os.environ.get("ENVELOPER_SERVICE") or cfg.service or "local")
    )
    ctx.obj["path"] = path if path is not None else ".env"
    ctx.obj["env_name"] = env_name
    ctx.obj["verbose"] = verbose


# ---------------------------------------------------------------------------
# init
# ---------------------------------------------------------------------------

@cli.command()
def init() -> None:
    """Configure the OS keychain for frictionless access.

    Platform-specific setup to minimize password prompts during builds.
    """
    import platform
    import shutil
    import subprocess

    system = platform.system()

    if system == "Darwin":
        console.print("[bold]macOS keychain setup[/bold]\n")

        # Disable auto-lock on the login keychain
        kc_path = Path.home() / "Library" / "Keychains" / "login.keychain-db"
        if kc_path.exists():
            try:
                subprocess.run(
                    ["security", "set-keychain-settings", str(kc_path)],
                    check=True,
                    capture_output=True,
                )
                console.print("[green]  Login keychain auto-lock disabled.[/green]")
            except subprocess.CalledProcessError:
                console.print(
                    "[yellow]  Could not disable keychain auto-lock "
                    "(may require unlocked keychain).[/yellow]"
                )
        else:
            console.print("[dim]  Login keychain not found at default path.[/dim]")

        # Enable Touch ID for sudo if pam_tid is available
        pam_sudo_local = Path("/etc/pam.d/sudo_local")
        tid_line = "auth       sufficient     pam_tid.so"
        if Path("/usr/lib/pam/pam_tid.so.2").exists() or Path(
            "/usr/lib/pam/pam_tid.so"
        ).exists():
            if pam_sudo_local.exists() and "pam_tid.so" in pam_sudo_local.read_text():
                console.print("[green]  Touch ID for sudo: already enabled.[/green]")
            else:
                console.print(
                    "\n  Touch ID can be used for sudo (useful for build commands)."
                )
                console.print(
                    f"  To enable, add this line to [bold]{pam_sudo_local}[/bold]:\n"
                )
                console.print(f"    {tid_line}\n")
                console.print(
                    "  Run: [dim]sudo sh -c 'echo \"auth       sufficient     "
                    "pam_tid.so\" > /etc/pam.d/sudo_local'[/dim]"
                )
        else:
            console.print("[dim]  Touch ID module not found (older macOS?).[/dim]")

        console.print(
            "\n[bold]Note:[/bold] On first keychain access, macOS shows an "
            '"allow this application" dialog.\n'
            "Click [bold]Always Allow[/bold] to prevent future prompts for "
            "this Python binary."
        )

    elif system == "Linux":
        console.print("[bold]Linux secret service setup[/bold]\n")

        # Check for a running secret service daemon
        has_dbus = shutil.which("dbus-send")
        if has_dbus:
            try:
                result = subprocess.run(
                    [
                        "dbus-send",
                        "--session",
                        "--print-reply",
                        "--dest=org.freedesktop.secrets",
                        "/org/freedesktop/secrets",
                        "org.freedesktop.DBus.Peer.Ping",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    console.print(
                        "[green]  Secret service daemon is running.[/green]"
                    )
                else:
                    console.print(
                        "[yellow]  Secret service daemon not responding.[/yellow]"
                    )
                    console.print(
                        "  Install gnome-keyring or kwallet and ensure it starts "
                        "at login."
                    )
            except (subprocess.TimeoutExpired, FileNotFoundError):
                console.print(
                    "[yellow]  Could not check secret service status.[/yellow]"
                )
        else:
            console.print(
                "[yellow]  dbus-send not found. "
                "Install dbus and a secret service (gnome-keyring or kwallet).[/yellow]"
            )

        console.print(
            "\n[bold]Note:[/bold] GNOME Keyring and KDE Wallet auto-unlock at "
            "login.\nNo repeated password prompts during builds."
        )

    elif system == "Windows":
        console.print("[bold]Windows credential setup[/bold]\n")
        console.print(
            "[green]  Windows Credential Locker is unlocked with your "
            "user session.[/green]\n"
            "  No additional setup needed. Secrets are accessible "
            "once you are logged in."
        )
        console.print(
            "\n[bold]Note:[/bold] If Windows Hello (fingerprint/face) is "
            "configured for login,\ncredentials are available after biometric "
            "unlock."
        )

    else:
        console.print(f"[yellow]Unknown platform: {system}[/yellow]")
        console.print(
            "Enveloper uses the 'keyring' library which supports "
            "most secret service backends."
        )

    console.print("\n[green]Init complete.[/green]")


# ---------------------------------------------------------------------------
# import
# ---------------------------------------------------------------------------

@cli.command("import")
@click.argument("file", required=False, type=click.Path(exists=False))
@click.option(
    "--format", "fmt",
    type=click.Choice(["env", "json", "yaml"]),
    default="env",
    help="Input format (env, json, yaml). Default: env.",
)
@click.pass_context
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

    # Parse the file based on format
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

        # Handle different formats:
        # 1. Simple: {key: value}
        # 2. Domain only: {domain: {key: value}}
        # 3. Domain + Project: {domain: {project: {key: value}}}
        pairs = {}
        if isinstance(data, dict):
            has_domains = False
            has_projects = False

            # Check if top-level keys are domains (values are dicts)
            for k, v in data.items():
                if isinstance(v, dict):
                    # Check if values are projects (dicts with non-dict values)
                    for pk, pv in v.items():
                        if isinstance(pv, dict):
                            has_projects = True
                        else:
                            has_domains = True
                        break
                    break

            if has_projects:
                # Format: {domain: {project: {key: value}}}
                for d_name, d_content in data.items():
                    if isinstance(d_content, dict):
                        for p_name, p_content in d_content.items():
                            if isinstance(p_content, dict):
                                for k, v in p_content.items():
                                    pairs[k] = str(v)
            elif has_domains:
                # Format: {domain: {key: value}}
                for d_name, d_content in data.items():
                    if isinstance(d_content, dict):
                        for k, v in d_content.items():
                            pairs[k] = str(v)
            else:
                # Format: {key: value}
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


# ---------------------------------------------------------------------------
# export
# ---------------------------------------------------------------------------

@cli.command("export")
@click.option(
    "--format", "fmt",
    type=click.Choice(["env", "dotenv", "json", "yaml"]),
    default="env",
    help="Output format.",
)
@click.option(
    "--output", "-o",
    type=click.Path(exists=False),
    default=None,
    help="Output file path (default: stdout).",
)
@click.pass_context
def export(ctx: click.Context, fmt: str, output: str | None) -> None:
    """Export secrets from the current service to stdout or file.

    Use with eval: eval "$(enveloper export -d aws)"
    Write to file: enveloper export -d aws -o .env
    From .env file: enveloper export --service file --path .env
    """
    project = ctx.obj["project"]
    domain = ctx.obj["domain"]
    service = ctx.obj["service"]

    store: SecretStore
    if service == "local" and domain is None:
        global_store = KeychainStore(project=project)
        domains = global_store.list_domains() or ["default"]
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
        use_local_key = service not in ("local", "file")  # strip domain/project when loading from cloud
        for key in store.list_keys():
            val = store.get(key)
            if val is not None:
                out_key = strip_domain_prefix(key) if use_local_key else key
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
                for key, value in sorted(pairs.items()):
                    if fmt == "env":
                        f.write(f"export {key}={_shell_escape(value)}\n")
                    else:
                        f.write(f"{key}={value}\n")
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
    store = _get_store(ctx)
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
    store = _get_store(ctx)
    if isinstance(store, KeychainStore):
        store.set_with_domain_tracking(key, value)
    else:
        store.set(key, value)
    console.print(f"[green]Set {key}[/green]")


@cli.command()
@click.argument("key")
@click.pass_context
def rm(ctx: click.Context, key: str) -> None:
    """Remove a single secret."""
    store = _get_store(ctx)
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
    domain = ctx.obj["domain"]  # None when user did not pass -d
    service = ctx.obj["service"]
    store: SecretStore

    if service == "local" and domain is None:
        # Keychain: show all domains (or default when none)
        global_store = KeychainStore(project=project)
        domains_to_show = global_store.list_domains() or ["default"]
        if not domains_to_show:
            console.print("[yellow]No secrets stored.[/yellow]")
            return
        table = Table(title=f"Secrets for project '{project}'")
        table.add_column("Project", style="cyan")
        table.add_column("Domain", style="cyan")
        table.add_column("Key", style="white")
        table.add_column("Value (masked)", style="dim")
        has_secrets = False
        for d in sorted(domains_to_show):
            store = _get_keychain(project, d)
            keys = store.list_keys()
            if not keys:
                table.add_row(project, d, "(empty)", "(empty)")
                has_secrets = True
                continue
            for key in sorted(keys):
                val = store.get(key)
                masked = _mask(val) if val else "(empty)"
                table.add_row(project, d, key, masked)
                has_secrets = True
        if not has_secrets:
            console.print("[yellow]No secrets stored.[/yellow]")
            return
        console.print(table)
    else:
        store = _get_store(ctx)
        keys = store.list_keys()
        title = f"Secrets ({service})"
        if service == "file":
            title = f"Secrets (file: {ctx.obj['path']})"
        table = Table(title=title)
        table.add_column("Key", style="white")
        table.add_column("Value (masked)", style="dim")
        if not keys:
            table.add_row("(empty)", "(empty)")
        else:
            for key in sorted(keys):
                val = store.get(key)
                masked = _mask(val) if val else "(empty)"
                table.add_row(key, masked)
        console.print(table)


def _mask(value: str) -> str:
    if len(value) <= 6:
        return "****"
    return value[:3] + "****" + value[-3:]


# ---------------------------------------------------------------------------
# clear
# ---------------------------------------------------------------------------

@cli.command()
@click.option(
    "--quiet", "-q",
    is_flag=True,
    help="Skip confirmation prompts (for automation).",
)
@click.pass_context
def clear(ctx: click.Context, quiet: bool) -> None:
    """Clear all secrets for the current service (local keychain, file, or cloud store)."""
    service = ctx.obj["service"]

    if not quiet:
        if not click.confirm("Are you sure you want to clear all secrets?"):
            raise click.Abort()

    store = _get_store(ctx)
    store.clear()
    if service == "local":
        domain = ctx.obj["domain_resolved"]
        console.print(f"[green]Cleared all secrets for service 'local' (domain '{domain}')[/green]")
    else:
        console.print(f"[green]Cleared all secrets for service '{service}'[/green]")


@cli.command("service")
def service_list() -> None:
    """List all available service providers in a table (local, file, then cloud stores)."""
    cloud = [n for n in sorted(list_store_names()) if n != "keychain"]
    table = Table(title="Service providers")
    table.add_column("Service", style="cyan")
    table.add_column("Description", style="white")
    table.add_column("Documentation", style="dim")
    # Local: one row per platform; each has two doc links (keyring + OS docs)
    for name, desc, platform_url in _LOCAL_PLATFORMS:
        table.add_row(name, desc, _local_doc_cell(_KEYRING_URL, platform_url))
    # File
    desc, url = _SERVICE_PROVIDER_INFO["file"]
    table.add_row("file", desc, _doc_link(url))
    # Cloud stores (aws, github, vault, gcp, azure, aliyun, and any plugins)
    for name in cloud:
        info = _SERVICE_PROVIDER_INFO.get(name)
        if info:
            desc, url = info
            table.add_row(name, desc, _doc_link(url))
        else:
            table.add_row(name, "(plugin)", "")
    console.print(table)


# ---------------------------------------------------------------------------
# push / pull
# ---------------------------------------------------------------------------

@cli.command()
@click.option("--from", "from_service", default="local", help="Source service to push from (default: local).")
@click.option("--prefix", default=None, help="Key prefix for the target store.")
@click.option("--profile", default=None, help="AWS profile (aws store).")
@click.option("--region", default=None, help="AWS region (aws store).")
@click.option("--repo", default=None, help="GitHub repo owner/name (github store).")
@click.pass_context
def push(
    ctx: click.Context,
    from_service: str,
    prefix: str | None,
    profile: str | None,
    region: str | None,
    repo: str | None,
) -> None:
    """Push secrets to a cloud store. Use global --service to specify the cloud store (e.g. --service aws)."""
    cloud_store = ctx.obj["service"]
    if cloud_store in ("local", "file"):
        raise click.UsageError("Push target must be a cloud store. Use --service aws, github, vault, gcp, azure, or aliyun.")
    domain = ctx.obj["domain_resolved"]
    cfg = ctx.obj["config"]
    env_name = ctx.obj["env_name"]
    path = ctx.obj.get("path", ".env")
    # Source: from_service (local, file, or cloud)
    orig_service = ctx.obj["service"]
    ctx.obj["service"] = from_service
    ctx.obj["path"] = path
    try:
        source = _get_store(ctx)
    finally:
        ctx.obj["service"] = orig_service
    keys = source.list_keys()
    if not keys:
        console.print("[yellow]No secrets to push.[/yellow]")
        return

    target = _make_cloud_store(
        cloud_store, cfg, domain, env_name,
        prefix=prefix, profile=profile, region=region, repo=repo,
    )

    count = 0
    for key in keys:
        val = source.get(key)
        if val is not None:
            target.set(key, val)
            count += 1
            if ctx.obj["verbose"]:
                console.print(f"  {key}")

    console.print(f"[green]Pushed {count} secret(s) to {cloud_store}[/green]")


@cli.command()
@click.option("--to", "to_service", default="local", help="Target service to pull into (default: local).")
@click.option("--prefix", default=None, help="Key prefix on the source store.")
@click.option("--profile", default=None, help="AWS profile (aws store).")
@click.option("--region", default=None, help="AWS region (aws store).")
@click.pass_context
def pull(
    ctx: click.Context,
    to_service: str,
    prefix: str | None,
    profile: str | None,
    region: str | None,
) -> None:
    """Pull secrets from a cloud store. Use global --service to specify the cloud store (e.g. --service aws)."""
    cloud_store = ctx.obj["service"]
    if cloud_store in ("local", "file"):
        raise click.UsageError("Pull source must be a cloud store. Use --service aws, vault, gcp, azure, or aliyun.")
    domain = ctx.obj["domain_resolved"]
    cfg = ctx.obj["config"]
    env_name = ctx.obj["env_name"]
    path = ctx.obj.get("path", ".env")
    source = _make_cloud_store(
        cloud_store, cfg, domain, env_name,
        prefix=prefix, profile=profile, region=region,
    )

    keys = source.list_keys()
    if not keys:
        console.print("[yellow]No secrets found in remote store.[/yellow]")
        return

    # Target: to_service (local, file, or cloud)
    orig_service = ctx.obj["service"]
    ctx.obj["service"] = to_service
    ctx.obj["path"] = path
    try:
        target = _get_store(ctx)
    finally:
        ctx.obj["service"] = orig_service
    count = 0
    for key in keys:
        val = source.get(key)
        if val is not None:
            local_key = strip_domain_prefix(key)  # strip domain/project for local env vars
            if isinstance(target, KeychainStore):
                target.set_with_domain_tracking(local_key, val)
            else:
                target.set(local_key, val)
            count += 1
            if ctx.obj["verbose"]:
                console.print(f"  {local_key}")

    console.print(f"[green]Pulled {count} secret(s) from {cloud_store}[/green]")


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
    domain_str = domain or "default"
    try:
        return resolve_make_cloud_store(
            store_name, cfg, domain_str, env_name,
            prefix=prefix, profile=profile, region=region, repo=repo,
        )
    except ValueError as e:
        raise click.UsageError(str(e))


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
        resolved_prefix = "/enveloper/"
    if not resolved_prefix.endswith("/"):
        resolved_prefix += "/"

    out = Console(file=sys.stdout, highlight=False)
    out.print("env:")
    out.print("  parameter-store:")
    for key in sorted(keys):
        out.print(f"    {key}: {resolved_prefix}{key}")
