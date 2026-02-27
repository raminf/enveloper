# Copyright (c) 2026 Ramin Firoozye
# SPDX-License-Identifier: AGPL-3.0-or-later

"""VaultStore -- push/pull secrets to HashiCorp Vault KV v2.

Requires ``hvac`` (install with ``pip install enveloper[vault]``).
Uses KV v2: one Vault path holds all keys for the given prefix/path.
"""

from __future__ import annotations

import os
from typing import Any

from enveloper.store import DEFAULT_NAMESPACE, DEFAULT_PREFIX, DEFAULT_VERSION, SecretStore

_MISSING_HVAC = (
    "hvac is required for the vault store. "
    "Install it with: pip install enveloper[vault]"
)


def _get_client(url: str | None = None, token: str | None = None) -> Any:
    try:
        import hvac  # type: ignore[import-untyped]
    except ModuleNotFoundError:
        raise RuntimeError(_MISSING_HVAC) from None

    base_url = url or os.environ.get("VAULT_ADDR", "http://127.0.0.1:8200")
    auth_token = token or os.environ.get("VAULT_TOKEN", "")
    client = hvac.Client(url=base_url, token=auth_token)
    if not client.is_authenticated():
        raise RuntimeError(
            "Vault client not authenticated. Set VAULT_TOKEN or VAULT_ADDR (and token via env or config)."
        )
    return client


def _vault_path_not_found(exc: BaseException) -> bool:
    try:
        import hvac.exceptions  # type: ignore[import-untyped]
        return isinstance(exc, hvac.exceptions.InvalidPath)
    except Exception:
        return "404" in str(exc) or "not found" in str(exc).lower()


class VaultStore(SecretStore):
    """Read/write secrets as a single KV v2 secret at a given path.

    All keys for this store are stored as one Vault secret at ``path``;
    the secret's ``data`` dict holds full composite key -> value.
    Key format: envr/{domain}/{project}/{version}/{name}.
    """

    service_name: str = "vault"
    service_display_name: str = "HashiCorp Vault KV v2"
    service_doc_url: str = "https://developer.hashicorp.com/vault/docs"

    default_namespace: str = "_default_"
    key_separator: str = "/"
    prefix: str = DEFAULT_PREFIX

    @classmethod
    def build_default_prefix(cls, domain: str, project: str) -> str:
        """Default Vault path: envr/{domain}/{project} (path separator /)."""
        d = cls.sanitize_key_segment(domain)
        p = cls.sanitize_key_segment(project)
        return f"{cls.prefix}/{d}/{p}"

    def __init__(
        self,
        path: str = "envr",
        mount_point: str = "secret",
        url: str | None = None,
        token: str | None = None,
        domain: str = DEFAULT_NAMESPACE,
        project: str = DEFAULT_NAMESPACE,
        version: str = DEFAULT_VERSION,
        prefix: str | None = None,
        **kwargs: object,
    ) -> None:
        # from_config passes prefix= (build_default_prefix result); use as path when present
        self._path = (prefix if prefix is not None else path).strip("/")
        self._mount_point = mount_point
        self._url = url
        self._token = token
        self._domain = domain
        self._project = project
        self._version = version
        self._client: Any = None

    @property
    def client(self) -> Any:
        if self._client is None:
            self._client = _get_client(self._url, self._token)
        return self._client

    def _read_data(self) -> dict[str, str]:
        try:
            resp = self.client.secrets.kv.v2.read_secret_version(
                path=self._path,
                mount_point=self._mount_point,
            )
        except Exception as e:
            if _vault_path_not_found(e):
                return {}
            raise
        data = resp.get("data", {}) or {}
        inner = data.get("data") or {}
        return dict(inner)

    def _write_data(self, data: dict[str, str]) -> None:
        self.client.secrets.kv.v2.create_or_update_secret(
            path=self._path,
            secret=data,
            mount_point=self._mount_point,
        )

    def _resolve_key(self, key: str) -> str:
        """Return full composite key; if key is short name, build full key with domain/project/version."""
        if self.parse_key(key) is not None:
            return key
        return self.build_key(
            name=key, project=self._project, domain=self._domain, version=self._version
        )

    def get(self, key: str) -> str | None:
        data = self._read_data()
        return data.get(self._resolve_key(key))

    def set(self, key: str, value: str) -> None:
        data = self._read_data()
        data[self._resolve_key(key)] = value
        self._write_data(data)

    def delete(self, key: str) -> None:
        data = self._read_data()
        full_key = self._resolve_key(key)
        if full_key in data:
            del data[full_key]
            self._write_data(data)

    def list_keys(self) -> list[str]:
        return sorted(self._read_data().keys())

    def clear(self) -> None:
        self._write_data({})
