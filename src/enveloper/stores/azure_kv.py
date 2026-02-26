"""AzureKvStore -- push/pull secrets to Azure Key Vault (Secrets).

Requires ``azure-keyvault-secrets`` and ``azure-identity``
(install with ``pip install enveloper[azure]``).
Uses DefaultAzureCredential (env, managed identity, Azure CLI, etc.).
"""

from __future__ import annotations

import re
from typing import Any

from enveloper.store import SecretStore

_MISSING_AZURE = (
    "azure-keyvault-secrets and azure-identity are required for the azure store. "
    "Install them with: pip install enveloper[azure]"
)

# Azure Key Vault secret names: 1-127 chars, [a-zA-Z0-9-]+ only
_SECRET_NAME_RE = re.compile(r"[^a-zA-Z0-9-]+")


def _sanitize_secret_name(key: str) -> str:
    """Replace invalid chars with hyphen for Azure secret name."""
    return _SECRET_NAME_RE.sub("-", key).strip("-").lower() or "key"


def _get_client(vault_url: str) -> Any:
    try:
        from azure.identity import DefaultAzureCredential  # type: ignore[import-untyped]
        from azure.keyvault.secrets import SecretClient  # type: ignore[import-untyped]
    except ModuleNotFoundError:
        raise RuntimeError(_MISSING_AZURE) from None
    credential = DefaultAzureCredential()
    return SecretClient(vault_url=vault_url, credential=credential)


class AzureKvStore(SecretStore):
    """Read/write secrets as Azure Key Vault secrets.

    Each key is stored as a separate secret; secret name = prefix + sanitized key
    (Azure allows only alphanumeric and hyphens). Uses DefaultAzureCredential.
    """

    def __init__(
        self,
        vault_url: str,
        prefix: str = "enveloper-",
    ) -> None:
        if not vault_url.startswith("https://"):
            vault_url = f"https://{vault_url}.vault.azure.net/"
        self._vault_url = vault_url.rstrip("/") + "/"
        self._prefix = prefix.strip("_").rstrip("-")
        if self._prefix:
            self._prefix = self._prefix + "-"
        self._prefix_lower = self._prefix.lower()
        self._client: Any = None

    @property
    def client(self) -> Any:
        if self._client is None:
            self._client = _get_client(self._vault_url)
        return self._client

    def _secret_name(self, key: str) -> str:
        return self._prefix + _sanitize_secret_name(key)

    def _name_to_key(self, secret_name: str) -> str:
        """Reverse sanitization is lossy; we return the stored name suffix as the key."""
        if secret_name.lower().startswith(self._prefix_lower):
            return secret_name[len(self._prefix) :]
        return secret_name

    def get(self, key: str) -> str | None:
        name = self._secret_name(key)
        try:
            secret = self.client.get_secret(name)
            return secret.value
        except Exception as e:
            if "SecretNotFound" in type(e).__name__ or "404" in str(e):
                return None
            raise

    def set(self, key: str, value: str) -> None:
        name = self._secret_name(key)
        self.client.set_secret(name, value)

    def delete(self, key: str) -> None:
        name = self._secret_name(key)
        try:
            self.client.begin_delete_secret(name).wait()
        except Exception as e:
            if "SecretNotFound" in type(e).__name__ or "404" in str(e):
                pass
            else:
                raise

    def list_keys(self) -> list[str]:
        keys: list[str] = []
        for prop in self.client.list_properties_of_secrets():
            name = getattr(prop, "name", "") or ""
            if name.lower().startswith(self._prefix_lower):
                keys.append(self._name_to_key(name))
        return sorted(set(keys))

    def clear(self) -> None:
        for key in self.list_keys():
            self.delete(key)
