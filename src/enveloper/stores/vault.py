"""VaultStore -- push/pull secrets to HashiCorp Vault KV v2.

Requires ``hvac`` (install with ``pip install enveloper[vault]``).
Uses KV v2: one Vault path holds all keys for the given prefix/path.
"""

from __future__ import annotations

import os
from typing import Any

from enveloper.store import SecretStore

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
    the secret's ``data`` dict holds key -> value. Path can include slashes
    (e.g. ``myapp/prod``). Uses ``VAULT_ADDR`` and ``VAULT_TOKEN`` if not
    passed in.
    """

    def __init__(
        self,
        path: str = "enveloper",
        mount_point: str = "secret",
        url: str | None = None,
        token: str | None = None,
    ) -> None:
        self._path = path.strip("/")
        self._mount_point = mount_point
        self._url = url
        self._token = token
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

    def get(self, key: str) -> str | None:
        data = self._read_data()
        return data.get(key)

    def set(self, key: str, value: str) -> None:
        data = self._read_data()
        data[key] = value
        self._write_data(data)

    def delete(self, key: str) -> None:
        data = self._read_data()
        if key in data:
            del data[key]
            self._write_data(data)

    def list_keys(self) -> list[str]:
        return sorted(self._read_data().keys())

    def clear(self) -> None:
        self._write_data({})
