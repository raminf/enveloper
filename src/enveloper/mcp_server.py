# Copyright (c) 2026 Ramin Firoozye
# SPDX-License-Identifier: AGPL-3.0-or-later

"""MCP (Model Context Protocol) server so LLMs can access env vars from enveloper (full CLI parity).

Tools are exposed with human-friendly descriptions (e.g. get secret, list keys, set secret).
Install: pip install enveloper[mcp]. Run: enveloper-mcp or uv run python -m enveloper.mcp_server.
Uses domain/project/version/service from arguments or ENVELOPER_* env / .enveloper.toml.
"""

from __future__ import annotations

import os

from enveloper.config import load_config
from enveloper.env_file import parse_env_file
from enveloper.resolve_store import get_store, make_cloud_store
from enveloper.sdk import dotenv_values
from enveloper.security import sanitize_file_access_path
from enveloper.stores.keychain import KeychainStore
from enveloper.util import key_to_export_name


def _resolve_domain_project(
    domain: str | None = None,
    project: str | None = None,
) -> tuple[str, str]:
    """Resolve domain and project from args, env, config."""
    cfg = load_config()
    p = project or os.environ.get("ENVELOPER_PROJECT") or cfg.project or "_default_"
    d = domain or os.environ.get("ENVELOPER_DOMAIN") or "_default_"
    return d, p


def _resolve_service(service: str | None = None) -> str:
    """Resolve service from args, env, config."""
    if service:
        return service
    cfg = load_config()
    return os.environ.get("ENVELOPER_SERVICE") or (cfg.service or "local")


def _resolve_version(version: str | None = None) -> str:
    """Resolve version from args, env, default."""
    if version:
        return version
    return os.environ.get("ENVELOPER_VERSION") or "1.0.0"


def _env_name() -> str | None:
    return os.environ.get("ENVELOPER_ENV") or os.environ.get("STILLUP_ENV_NAME")


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------


def get_secret(
    key: str,
    domain: str | None = None,
    project: str | None = None,
    version: str | None = None,
    service: str | None = None,
    path: str = ".env",
) -> str:
    """Get a secret value by key.

    Returns the value or a short message if not found. Domain, project, version, and
    service default from ENVELOPER_* env or .enveloper.toml.
    """
    try:
        d, p = _resolve_domain_project(domain, project)
        svc = _resolve_service(service)
        ver = _resolve_version(version)
        values = dotenv_values(domain=d, project=p, service=svc, path=path, version=ver)
        if key in values and values[key]:
            return values[key]
        return f"Secret not found for key {key!r} (domain={d!r}, project={p!r}, service={svc!r})."
    except Exception as e:
        return f"Something went wrong: {e!s}"


def list_keys(
    domain: str | None = None,
    project: str | None = None,
    version: str | None = None,
    service: str | None = None,
    path: str = ".env",
) -> list[str]:
    """List key names (no values) for the given scope.

    Use domain, project, version, service (and path when service is file) to scope.
    Defaults from ENVELOPER_* env and .enveloper.toml.
    """
    try:
        d, p = _resolve_domain_project(domain, project)
        svc = _resolve_service(service)
        ver = _resolve_version(version)
        cfg = load_config()
        store = get_store(svc, p, d, cfg, path=path, version=ver)
        keys = store.list_keys()
        if svc not in ("local", "file"):
            return [key_to_export_name(store, k) for k in keys]
        return sorted(keys)
    except Exception:
        return []


def list_domains(
    project: str | None = None,
    service: str | None = None,
) -> list[str]:
    """List domain names that have secrets.

    For local keychain, optionally limit by project; otherwise all domains.
    For cloud stores, uses default project from config or env.
    """
    try:
        svc = _resolve_service(service)
        if svc != "local":
            _, p = _resolve_domain_project(None, project)
            cfg = load_config()
            store = get_store(svc, p, "_default_", cfg)
            return sorted(store.list_domains())
        if project:
            store = KeychainStore(project=project or "_default_")
            return sorted(store.list_domains())
        all_d = KeychainStore.list_all_domains()
        domains = set()
        for _proj, doms in all_d.items():
            domains.update(doms)
        return sorted(domains)
    except Exception:
        return []


def list_projects(
    domain: str | None = None,
    project: str | None = None,
    service: str | None = None,
) -> list[str]:
    """List project names that have secrets in the given domain.

    For local keychain, domain defaults to _default_. For cloud stores,
    uses resolved domain and project from config or env.
    """
    try:
        d, _p = _resolve_domain_project(domain, project)
        svc = _resolve_service(service)
        if svc != "local":
            cfg = load_config()
            store = get_store(svc, _p, d, cfg)
            return sorted(store.list_projects(d))
        return sorted(KeychainStore.list_projects_for_domain(d))
    except Exception:
        return []


def list_services() -> list[str]:
    """List available store names (e.g. keychain, file, aws, gcp, azure, vault, github)."""
    try:
        from enveloper.stores import get_service_entries

        return [name for name, _ in get_service_entries()]
    except Exception:
        return ["keychain", "file"]


# ---------------------------------------------------------------------------
# Write
# ---------------------------------------------------------------------------


def set_secret(
    key: str,
    value: str,
    domain: str | None = None,
    project: str | None = None,
    version: str | None = None,
    service: str | None = None,
    path: str = ".env",
) -> str:
    """Set a secret. Returns a short status message."""
    try:
        d, p = _resolve_domain_project(domain, project)
        svc = _resolve_service(service)
        ver = _resolve_version(version)
        cfg = load_config()
        store = get_store(svc, p, d, cfg, path=path, version=ver)
        store.set_with_tracking(key, value)
        return f"Set {key}"
    except Exception as e:
        return f"Something went wrong: {e!s}"


def delete_secret(
    key: str,
    domain: str | None = None,
    project: str | None = None,
    version: str | None = None,
    service: str | None = None,
    path: str = ".env",
) -> str:
    """Remove a secret. Returns a short status message."""
    try:
        d, p = _resolve_domain_project(domain, project)
        svc = _resolve_service(service)
        ver = _resolve_version(version)
        cfg = load_config()
        store = get_store(svc, p, d, cfg, path=path, version=ver)
        store.delete_with_tracking(key)
        return f"Removed {key}"
    except Exception as e:
        return f"Something went wrong: {e!s}"


def import_from_file(
    file_path: str,
    domain: str | None = None,
    project: str | None = None,
    version: str | None = None,
    service: str | None = None,
    path: str = ".env",
) -> str:
    """Import key-value pairs from a .env file into the store.

    file_path: path to the .env file. Only env format is supported (KEY=value lines).
    Defaults for domain/project/version/service from ENVELOPER_* and config.
    When service=file, path is the target .env file to write to; otherwise path is ignored for import source.
    """
    try:
        p = sanitize_file_access_path(file_path)
        if not p.is_file():
            return f"File not found: {file_path!r}"
        pairs = parse_env_file(p)
        if not pairs:
            return "No variables found in file."
        d, proj = _resolve_domain_project(domain, project)
        svc = _resolve_service(service)
        ver = _resolve_version(version)
        cfg = load_config()
        store = get_store(svc, proj, d, cfg, path=path, version=ver)
        for k, v in pairs.items():
            store.set_with_tracking(k, v)
        return f"Imported {len(pairs)} variable(s) from {file_path}"
    except Exception as e:
        return f"Something went wrong: {e!s}"


def clear_scope(
    domain: str | None = None,
    project: str | None = None,
    service: str | None = None,
    path: str = ".env",
    clear_all: bool = False,
) -> str:
    """Clear all secrets for a domain/project, or every secret when clear_all=True.

    No confirmation; use with care. Returns a short status message.
    """
    try:
        d, p = _resolve_domain_project(domain, project)
        svc = _resolve_service(service)
        cfg = load_config()

        if clear_all:
            if svc == "local":
                for proj in KeychainStore.list_all_projects() or ["_default_"]:
                    proj_store = KeychainStore(project=proj)
                    for dom in proj_store.list_domains() or ["_default_"]:
                        KeychainStore(project=proj, domain=dom).clear()
                    KeychainStore.unregister_global_project(proj)
            else:
                from enveloper.stores import get_store_class

                store_cls = get_store_class(svc)
                broad_prefix = f"{store_cls.prefix}{store_cls.key_separator}"
                store = make_cloud_store(svc, cfg, "_default_", _env_name(), project="_default_", prefix=broad_prefix)
                store.clear()
                store.clear_metadata()
            return f"Cleared ALL secrets for every project and domain ({svc})"
        if svc == "local":
            store = KeychainStore(project=p, domain=d)
            store.clear()
            if not KeychainStore(project=p).list_domains():
                KeychainStore.unregister_global_project(p)
        else:
            store = get_store(svc, p, d, cfg, path=path)
            store.clear()
            if svc not in ("local", "file"):
                store.clear_metadata()
        return f"Cleared secrets for domain '{d}', project '{p}'"
    except Exception as e:
        return f"Something went wrong: {e!s}"


# ---------------------------------------------------------------------------
# Export / unexport
# ---------------------------------------------------------------------------


def export_env(
    domain: str | None = None,
    project: str | None = None,
    version: str | None = None,
    service: str | None = None,
    path: str = ".env",
    format: str = "dotenv",
) -> str:
    """Export all secrets for the scope as env lines.

    format: 'dotenv' (KEY=value) or 'unix' (export KEY='value').
    Use in scripts or to inject into a process. Defaults from ENVELOPER_* and config.
    """
    try:
        d, p = _resolve_domain_project(domain, project)
        ver = _resolve_version(version)
        values = dotenv_values(domain=d, project=p, service=_resolve_service(service), path=path, version=ver)
        if not values:
            return "# no secrets for this scope"
        if format == "unix":
            lines = []
            for k, v in sorted(values.items()):
                safe = str(v).replace("'", "'\"'\"'")
                lines.append(f"export {k}='{safe}'")
            return "\n".join(lines)
        lines = []
        for k, v in sorted(values.items()):
            val = str(v)
            if "\n" in val or '"' in val or " " in val or "=" in val:
                val = '"' + val.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'
            lines.append(f"{k}={val}")
        return "\n".join(lines)
    except Exception as e:
        return f"# Something went wrong: {e}"


def unexport_env(
    domain: str | None = None,
    project: str | None = None,
    version: str | None = None,
    service: str | None = None,
    path: str = ".env",
    format: str = "unix",
) -> str:
    """Output shell unset commands for all variables in the scope.

    Use with eval to clear env vars after export. format: 'unix' (unset KEY) or 'win' (Remove-Item Env:KEY).
    """
    try:
        d, p = _resolve_domain_project(domain, project)
        svc = _resolve_service(service)
        ver = _resolve_version(version)
        cfg = load_config()
        store = get_store(svc, p, d, cfg, path=path, version=ver)
        keys = store.list_keys()
        if svc not in ("local", "file"):
            keys = [key_to_export_name(store, k) for k in keys]
        keys = sorted(set(keys))
        if format == "win":
            return "\n".join(f"Remove-Item Env:{k}" for k in keys) if keys else "# no keys"
        return "\n".join(f"unset {k}" for k in keys) if keys else "# no keys"
    except Exception as e:
        return f"# Something went wrong: {e}"


# ---------------------------------------------------------------------------
# Push / pull
# ---------------------------------------------------------------------------


def push_to_service(
    cloud_service: str,
    from_service: str = "local",
    domain: str | None = None,
    project: str | None = None,
    path: str = ".env",
) -> str:
    """Push secrets from a source store (default: local keychain) to a cloud store.

    cloud_service: aws, github, gcp, azure, vault, or aliyun.
    Returns a short status message.
    """
    if cloud_service in ("local", "file"):
        return "Push target must be a cloud store (e.g. aws, github, gcp, azure, vault, aliyun)."
    try:
        d, p = _resolve_domain_project(domain, project)
        cfg = load_config()
        source = get_store(from_service, p, d, cfg, path=path)
        keys = source.list_keys()
        if not keys:
            return "No secrets to push."
        target = make_cloud_store(cloud_service, cfg, d, _env_name(), project=p)
        from enveloper.stores.github import GitHubStore

        version = getattr(source, "_version", None) or _resolve_version(None)
        count = 0
        for key in keys:
            val = source.get(key)
            if val is not None:
                name = key_to_export_name(source, key)
                if isinstance(target, GitHubStore):
                    target.set_with_tracking(name, val)
                else:
                    target_key = target.build_key(name=name, domain=d, project=p, version=version)
                    target.set_with_tracking(target_key, val)
                count += 1
        return f"Pushed {count} secret(s) to {cloud_service}"
    except Exception as e:
        return f"Something went wrong: {e!s}"


def pull_from_service(
    cloud_service: str,
    to_service: str = "local",
    domain: str | None = None,
    project: str | None = None,
    path: str = ".env",
) -> str:
    """Pull secrets from a cloud store into a target store (default: local keychain).

    cloud_service: aws, gcp, azure, vault, or aliyun (github is push-only).
    Returns a short status message.
    """
    if cloud_service in ("local", "file"):
        return "Pull source must be a cloud store (e.g. aws, gcp, azure, vault, aliyun)."
    try:
        d, p = _resolve_domain_project(domain, project)
        cfg = load_config()
        source = make_cloud_store(cloud_service, cfg, d, _env_name(), project=p)
        keys = source.list_keys()
        if not keys:
            return "No secrets found in remote store."
        target = get_store(to_service, p, d, cfg, path=path)
        count = 0
        for key in keys:
            val = source.get(key)
            if val is not None:
                local_key = key_to_export_name(source, key)
                target.set_with_tracking(local_key, val)
                count += 1
        return f"Pulled {count} secret(s) from {cloud_service}"
    except Exception as e:
        return f"Something went wrong: {e!s}"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Run the MCP server (stdio transport)."""
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as e:
        raise SystemExit(
            "enveloper MCP server requires the mcp package. Install with: pip install enveloper[mcp]"
        ) from e

    mcp = FastMCP(
        "Enveloper",
        json_response=True,
    )

    mcp.tool()(get_secret)
    mcp.tool()(set_secret)
    mcp.tool()(delete_secret)
    mcp.tool()(list_keys)
    mcp.tool()(list_domains)
    mcp.tool()(list_projects)
    mcp.tool()(list_services)
    mcp.tool()(import_from_file)
    mcp.tool()(export_env)
    mcp.tool()(unexport_env)
    mcp.tool()(clear_scope)
    mcp.tool()(push_to_service)
    mcp.tool()(pull_from_service)

    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
