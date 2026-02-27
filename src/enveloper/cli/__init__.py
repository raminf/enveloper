# Copyright (c) 2026 Ramin Firoozye
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Enveloper CLI -- manage .env secrets via system keychain + cloud stores.

The CLI is split into per-command modules under this package.  The ``cli``
click group, shared helpers (``console``, ``common_options``, ``_get_store``,
etc.) live here so every command module can import them.
"""

from __future__ import annotations

import functools
import os
from typing import TYPE_CHECKING

import click
from rich.console import Console
from rich.style import Style
from rich.table import Table
from rich.text import Text

from enveloper import __version__
from enveloper.config import load_config
from enveloper.resolve_store import get_store as resolve_get_store
from enveloper.resolve_store import make_cloud_store as resolve_make_cloud_store
from enveloper.store import DEFAULT_VERSION, SecretStore
from enveloper.stores import list_store_names
from enveloper.stores.github import GitHubStore
from enveloper.stores.keychain import KeychainStore
from enveloper.stores import get_service_entries
from enveloper.util import key_to_export_name, strip_domain_prefix

if TYPE_CHECKING:
    pass

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

console = Console(stderr=True)


def _doc_link(url: str, label: str = "Doc Link") -> Text:
    """Rich Text with an OSC 8 hyperlink for terminal clickability."""
    return Text(label, style=Style(link=url))


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _get_keychain(project: str, domain: str | None) -> KeychainStore:
    return KeychainStore(project=project, domain=domain)


def _get_store(ctx: click.Context) -> SecretStore:
    """Return the current store for get/set/list/import/export."""
    service = ctx.obj.get("service", "local")
    project = ctx.obj["project"]
    domain = ctx.obj.get("domain_resolved", "_default_")
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


def _make_cloud_store(
    store_name: str,
    cfg: object,
    project: str | None,
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
    domain_str = domain or "_default_"
    project_str = project or "_default_"
    try:
        return resolve_make_cloud_store(
            store_name, cfg, domain_str, env_name,
            project=project_str,
            prefix=prefix, profile=profile, region=region, repo=repo,
        )
    except ValueError as e:
        raise click.UsageError(str(e))


def _mask(value: str) -> str:
    if len(value) <= 6:
        return "****"
    return value[:3] + "****" + value[-3:]


def _merge_common(
    ctx: click.Context,
    project: str | None,
    domain: str | None,
    service: str | None,
    version: str | None = None,
) -> None:
    """Merge subcommand-level project/domain/service/version into ctx.obj."""
    if project is not None:
        ctx.obj["project"] = project
    if domain is not None:
        ctx.obj["domain"] = domain
    ctx.obj["domain_resolved"] = ctx.obj["domain"] or "_default_"
    if service is not None:
        ctx.obj["service"] = service
    if version is not None:
        ctx.obj["version"] = version


def common_options(f: object) -> object:
    """Add --project, --domain, --service, --version to a command."""
    @functools.wraps(f)
    @click.option(
        "--service", "-s", default=None,
        help="Backend: local, file (.env), or cloud. Default: ENVELOPER_SERVICE or config, else local.",
    )
    @click.option("--domain", "-d", default=None, help="Domain / subsystem scope (default: from ENVELOPER_DOMAIN env var).")
    @click.option("--project", "-p", default=None, help="Project namespace (default: from config or ENVELOPER_PROJECT env var).")
    @click.option("--version", default=None, help="Version (semver format, default: 1.0.0).")
    @click.pass_context
    def wrapper(
        ctx: click.Context,
        project: str | None,
        domain: str | None,
        service: str | None,
        version: str | None,
        *args: object,
        **kwargs: object,
    ) -> object:
        _merge_common(ctx, project, domain, service)
        if version is not None:
            ctx.obj["version"] = version
        return f(ctx, *args, **kwargs)
    return wrapper


# ---------------------------------------------------------------------------
# Top-level click group
# ---------------------------------------------------------------------------

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
    cfg = load_config()
    ctx.ensure_object(dict)
    ctx.obj["config"] = cfg
    ctx.obj["project"] = project or os.environ.get("ENVELOPER_PROJECT") or cfg.project
    ctx.obj["domain"] = domain or os.environ.get("ENVELOPER_DOMAIN")
    ctx.obj["domain_resolved"] = ctx.obj["domain"] or "_default_"
    ctx.obj["service"] = (
        service
        if service is not None
        else (os.environ.get("ENVELOPER_SERVICE") or cfg.service or "local")
    )
    ctx.obj["path"] = path if path is not None else ".env"
    ctx.obj["env_name"] = env_name
    ctx.obj["verbose"] = verbose


# ---------------------------------------------------------------------------
# Register all command modules (import triggers @cli.command registration)
# ---------------------------------------------------------------------------

from enveloper.cli import (  # noqa: E402, F401
    init_cmd,
    import_cmd,
    export_cmd,
    crud_cmd,
    list_cmd,
    clear_cmd,
    service_cmd,
    push_pull_cmd,
    generate_cmd,
)
