# Copyright (c) 2026 Ramin Firoozye
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Resolve the secret store for a given service (local, file, or cloud). Used by CLI and SDK."""

from __future__ import annotations

from typing import TYPE_CHECKING

from enveloper.store import DEFAULT_NAMESPACE, DEFAULT_VERSION
from enveloper.stores import get_store_class
from enveloper.stores.file_store import FileStore
from enveloper.stores.keychain import KeychainStore

if TYPE_CHECKING:
    from enveloper.config import EnveloperConfig
    from enveloper.store import SecretStore


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
    version: str | None = None,
) -> SecretStore:
    """Instantiate a cloud store with resolved options. Raises ValueError on missing config.

    When prefix is not provided, uses the store's plugin API (default_namespace and
    build_default_prefix) so each provider controls its own key namespace and separator.
    """
    store_cls = get_store_class(store_name)
    default_ns = getattr(store_cls, "default_namespace", DEFAULT_NAMESPACE)
    domain_str = domain or default_ns
    project_str = project or default_ns
    version_str = version or DEFAULT_VERSION

    # Build kwargs for store constructor (version and store-specific; domain/project passed to from_config)
    kwargs: dict[str, object] = {"version": version_str}

    # Add store-specific kwargs based on store name
    if store_name == "aws":
        if profile is not None:
            kwargs["profile"] = profile
        if region is not None:
            kwargs["region"] = region
    elif store_name == "github":
        if repo is not None:
            kwargs["repo"] = repo
    elif store_name == "vault":
        if cfg.vault_url is not None:
            kwargs["url"] = cfg.vault_url
        if cfg.vault_mount is not None:
            kwargs["mount_point"] = cfg.vault_mount
    elif store_name == "gcp":
        if cfg.gcp_project is not None:
            kwargs["project_id"] = cfg.gcp_project
    elif store_name == "azure":
        if cfg.azure_vault_url is not None:
            kwargs["vault_url"] = cfg.azure_vault_url
    elif store_name == "aliyun":
        if cfg.aliyun_region_id is not None:
            kwargs["region_id"] = cfg.aliyun_region_id
        if cfg.aliyun_access_key_id is not None:
            kwargs["access_key_id"] = cfg.aliyun_access_key_id
        if cfg.aliyun_access_key_secret is not None:
            kwargs["access_key_secret"] = cfg.aliyun_access_key_secret

    # Use the store's from_config classmethod to create the instance
    # This allows each store to encapsulate its own configuration logic
    return store_cls.from_config(
        domain=domain_str,
        project=project_str,
        config=cfg,
        prefix=prefix,
        env_name=env_name,
        **kwargs,
    )


def get_store(
    service: str,
    project: str,
    domain: str,
    config: EnveloperConfig,
    *,
    path: str = ".env",
    env_name: str | None = None,
    version: str | None = None,
) -> SecretStore:
    """Return the secret store for the given service (local, file, or cloud name)."""
    if service == "local":
        return KeychainStore(project=project, domain=domain, version=version or DEFAULT_VERSION)
    if service == "file":
        return FileStore(path=path)
    return make_cloud_store(
        service, config, domain, env_name,
        project=project,
        prefix=None, profile=None, region=None, repo=None,
        version=version,
    )

