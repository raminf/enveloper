# Copyright (c) 2026 Ramin Firoozye
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Resolve the secret store for a given service (local, file, or cloud). Used by CLI and SDK."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from enveloper.security import sanitize_file_access_path, sanitize_namespace_segment
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
    domain_str = sanitize_namespace_segment(domain or default_ns, default=default_ns, field_name="domain")
    project_str = sanitize_namespace_segment(project or default_ns, default=default_ns, field_name="project")
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
        from enveloper.stores.gcp_sm import _detect_gcp_project, resolve_gcp_project_id

        # GCP project_id is the Google Cloud project, NOT the enveloper --project namespace.
        # The configured value may be a project ID *or* a human-friendly display name
        # (the "Project name" shown in the GCP console). resolve_gcp_project_id handles both.
        gcp_project_id: str | None
        if cfg.gcp_project:
            gcp_project_id = resolve_gcp_project_id(cfg.gcp_project)
        else:
            gcp_project_id = _detect_gcp_project()
        if not gcp_project_id:
            raise ValueError(
                "GCP project ID is required but could not be determined.\n"
                "Set one of:\n"
                "  - ENVELOPER_GCP_PROJECT or GOOGLE_CLOUD_PROJECT env var\n"
                "  - [enveloper.gcp] project = \"...\" in .enveloper.toml\n"
                "    (accepts a project ID or the Project Name from the GCP console)\n"
                "  - gcloud config set project <project-id>"
            )
        kwargs["project_id"] = gcp_project_id
    elif store_name == "azure":
        vault_url = cfg.azure_vault_url or os.environ.get("ENVELOPER_AZURE_VAULT_URL", "").strip()
        if vault_url:
            kwargs["vault_url"] = vault_url
        else:
            raise ValueError(
                "Azure Key Vault URL is required but could not be determined.\n"
                "Set one of:\n"
                "  - ENVELOPER_AZURE_VAULT_URL env var (e.g. https://my-vault.vault.azure.net/)\n"
                "  - [enveloper.azure] vault_url = \"...\" in .enveloper.toml"
            )
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
        return FileStore(path=sanitize_file_access_path(path))
    return make_cloud_store(
        service, config, domain, env_name,
        project=project,
        prefix=None, profile=None, region=None, repo=None,
        version=version,
    )
