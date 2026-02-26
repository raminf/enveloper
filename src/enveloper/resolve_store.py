"""Resolve the secret store for a given service (local, file, or cloud). Used by CLI and SDK."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from enveloper.store import DEFAULT_NAMESPACE
from enveloper.stores import get_store_class
from enveloper.stores.file_store import FileStore
from enveloper.stores.keychain import KeychainStore

if TYPE_CHECKING:
    from enveloper.config import EnveloperConfig
    from enveloper.store import SecretStore


def _default_prefix_from_store(store_cls: type, domain: str, project: str) -> str:
    """Use the store's plugin API to build default prefix/path, or fallback for unknown stores."""
    builder = getattr(store_cls, "build_default_prefix", None)
    if builder is not None and callable(builder):
        return builder(domain, project)
    return "/enveloper/"


def make_cloud_store(
    store_name: str,
    cfg: EnveloperConfig,
    domain: str,
    env_name: str | None,
    *,
    project: str | None = None,
    prefix: str | None = None,
    profile: str | None = None,
    region: str | None = None,
    repo: str | None = None,
) -> SecretStore:
    """Instantiate a cloud store with resolved options. Raises ValueError on missing config.

    When prefix is not provided, uses the store's plugin API (default_namespace and
    build_default_prefix) so each provider controls its own key namespace and separator.
    """
    store_cls = get_store_class(store_name)
    default_ns = getattr(store_cls, "default_namespace", DEFAULT_NAMESPACE)
    domain_str = domain or default_ns
    project_str = project or default_ns
    default_prefix = _default_prefix_from_store(store_cls, domain_str, project_str)

    if store_name == "aws":
        resolved_prefix = prefix
        if resolved_prefix is None and domain_str:
            resolved_prefix = cfg.resolve_ssm_prefix(domain_str, env_name)
        if resolved_prefix is None:
            resolved_prefix = default_prefix
        return store_cls(
            prefix=resolved_prefix,
            profile=profile or cfg.aws_profile,
            region=region or cfg.aws_region,
        )
    elif store_name == "github":
        gh_prefix = prefix if prefix is not None else cfg.github_prefix
        if gh_prefix == "" or gh_prefix is None:
            gh_prefix = default_prefix
        return store_cls(prefix=gh_prefix, repo=repo)
    elif store_name == "vault":
        resolved_path = prefix
        if resolved_path is None and domain_str:
            resolved_path = cfg.resolve_ssm_prefix(domain_str, env_name) or ""
        if resolved_path is None or not resolved_path.strip():
            resolved_path = default_prefix
        resolved_path = (resolved_path or "enveloper").strip("/") or "enveloper"
        return store_cls(
            path=resolved_path,
            mount_point=cfg.vault_mount,
            url=cfg.vault_url,
        )
    elif store_name == "gcp":
        resolved_prefix = prefix
        if resolved_prefix is None and domain_str:
            resolved_prefix = cfg.resolve_ssm_prefix(domain_str, env_name)
        if resolved_prefix is None:
            resolved_prefix = default_prefix
        else:
            resolved_prefix = resolved_prefix.strip("/").replace("/", "-")
            if resolved_prefix:
                resolved_prefix = resolved_prefix + "-"
        project_id = cfg.gcp_project or ""
        if not project_id:
            project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "enveloper")
        return store_cls(project_id=project_id, prefix=resolved_prefix)
    elif store_name == "azure":
        vault_url = cfg.azure_vault_url or ""
        if not vault_url:
            vault_url = os.environ.get("AZURE_VAULT_URL", "")
        if not vault_url:
            raise ValueError(
                "Azure Key Vault store requires [enveloper.azure] vault_url in config or AZURE_VAULT_URL env."
            )
        resolved_prefix = prefix
        if resolved_prefix is None and domain_str:
            resolved_prefix = cfg.resolve_ssm_prefix(domain_str, env_name)
        if resolved_prefix is None:
            resolved_prefix = default_prefix
        else:
            resolved_prefix = resolved_prefix.strip("/").replace("/", "-")
            if resolved_prefix:
                resolved_prefix = resolved_prefix + "-"
        return store_cls(vault_url=vault_url, prefix=resolved_prefix)
    elif store_name == "aliyun":
        resolved_prefix = prefix
        if resolved_prefix is None and domain_str:
            resolved_prefix = cfg.resolve_ssm_prefix(domain_str, env_name)
        if resolved_prefix is None:
            resolved_prefix = default_prefix
        else:
            resolved_prefix = resolved_prefix.strip("/").replace("/", "-")
            if resolved_prefix:
                resolved_prefix = resolved_prefix + "-"
        return store_cls(
            prefix=resolved_prefix,
            region_id=cfg.aliyun_region_id,
            access_key_id=cfg.aliyun_access_key_id,
            access_key_secret=cfg.aliyun_access_key_secret,
        )
    else:
        return store_cls()


def get_store(
    service: str,
    project: str,
    domain: str,
    config: EnveloperConfig,
    *,
    path: str = ".env",
    env_name: str | None = None,
) -> SecretStore:
    """Return the secret store for the given service (local, file, or cloud name)."""
    if service == "local":
        return KeychainStore(project=project, domain=domain)
    if service == "file":
        return FileStore(path=path)
    return make_cloud_store(
        service, config, domain, env_name,
        project=project,
        prefix=None, profile=None, region=None, repo=None,
    )
