"""AzureKvStore -- push/pull secrets to Azure Key Vault (Secrets).

Requires ``azure-keyvault-secrets`` and ``azure-identity``
(install with ``pip install enveloper[azure]``).
Uses DefaultAzureCredential (env, managed identity, Azure CLI, etc.).
"""

from __future__ import annotations

import re
from typing import Any

from enveloper.store import DEFAULT_NAMESPACE, DEFAULT_PREFIX, DEFAULT_VERSION, SecretStore

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

    Each key is stored as a separate secret; secret name = sanitized full composite key
    (Azure allows only alphanumeric and hyphens). Key format: envr--{domain}--{project}--{version}--{name}.
    """

    service_name: str = "azure"
    service_display_name: str = "Azure Key Vault"
    service_doc_url: str = "https://learn.microsoft.com/en-us/azure/key-vault/"

    default_namespace: str = "default"  # Azure disallows _ in names; use 'default'
    key_separator: str = "--"
    prefix: str = DEFAULT_PREFIX

    @classmethod
    def build_default_prefix(cls, domain: str, project: str) -> str:
        """Default prefix: envr--{domain}--{project}-- (separator --)."""
        d = cls.sanitize_key_segment(domain)
        p = cls.sanitize_key_segment(project)
        return f"{cls.prefix}--{d}--{p}--"

    def __init__(
        self,
        vault_url: str,
        prefix: str = "envr--",
        domain: str = DEFAULT_NAMESPACE,
        project: str = DEFAULT_NAMESPACE,
        version: str = DEFAULT_VERSION,
        **kwargs: object,
    ) -> None:
        if not vault_url.startswith("https://"):
            vault_url = f"https://{vault_url}.vault.azure.net/"
        self._vault_url = vault_url.rstrip("/") + "/"
        self._path_prefix = prefix  # e.g. envr--domain--project-- for list filter
        self._domain = domain
        self._project = project
        self._version = version
        self._client: Any = None

    @property
    def client(self) -> Any:
        if self._client is None:
            self._client = _get_client(self._vault_url)
        return self._client

    def _resolve_key(self, key: str) -> str:
        """Return full composite key; if key is short name, build full key with domain/project/version."""
        if self.parse_key(key) is not None:
            return key
        return self.build_key(
            name=key, project=self._project, domain=self._domain, version=self._version
        )

    def _secret_name(self, key: str) -> str:
        """Azure secret name = sanitized full composite key (no extra prefix)."""
        return _sanitize_secret_name(self._resolve_key(key))

    def _name_to_key(self, secret_name: str) -> str:
        """Return secret name as key (get() accepts sanitized key)."""
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
        """Return keys (sanitized full composite) so get(key) works."""
        keys: list[str] = []
        filter_prefix = _sanitize_secret_name(self._path_prefix.rstrip("-")).lower()
        for prop in self.client.list_properties_of_secrets():
            name = getattr(prop, "name", "") or ""
            if filter_prefix and name.lower().startswith(filter_prefix):
                keys.append(self._name_to_key(name))
            elif not filter_prefix and name.lower().startswith("envr"):
                keys.append(self._name_to_key(name))
        return sorted(set(keys))

