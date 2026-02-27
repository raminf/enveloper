# Copyright (c) 2026 Ramin Firoozye
# SPDX-License-Identifier: AGPL-3.0-or-later

"""GcpSmStore -- push/pull secrets to Google Cloud Secret Manager.

Requires ``google-cloud-secret-manager`` (install with ``pip install enveloper[gcp]``).
Uses Application Default Credentials or GOOGLE_APPLICATION_CREDENTIALS.
"""

from __future__ import annotations

import re
from typing import Any

from enveloper.store import DEFAULT_NAMESPACE, DEFAULT_PREFIX, DEFAULT_VERSION, SecretStore

_MISSING_GCP = (
    "google-cloud-secret-manager is required for the gcp store. "
    "Install it with: pip install enveloper[gcp]"
)

# GCP secret ID: 1-255 chars, [a-zA-Z0-9_-]+
_SECRET_ID_RE = re.compile(r"[^a-zA-Z0-9_-]+")


def _sanitize_secret_id(key: str) -> str:
    """Replace invalid chars with underscore for GCP secret ID."""
    return _SECRET_ID_RE.sub("_", key).strip("_") or "key"


def _get_client() -> Any:
    try:
        from google.cloud import secretmanager  # type: ignore[import-untyped]
    except ModuleNotFoundError:
        raise RuntimeError(_MISSING_GCP) from None
    return secretmanager.SecretManagerServiceClient()


class GcpSmStore(SecretStore):
    """Read/write secrets as Google Cloud Secret Manager secrets.

    Each key is stored as a separate secret; secret ID = sanitized full composite key.
    Key format: envr--{domain}--{project}--{version}--{name}.
    """

    service_name: str = "gcp"
    service_display_name: str = "Google Cloud Secret Manager"
    service_doc_url: str = "https://cloud.google.com/secret-manager/docs"

    default_namespace: str = "_default_"
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
        project_id: str,
        prefix: str = "envr--",
        domain: str = DEFAULT_NAMESPACE,
        project: str = DEFAULT_NAMESPACE,
        version: str = DEFAULT_VERSION,
        **kwargs: object,
    ) -> None:
        self._project_id = project_id
        self._path_prefix = prefix
        self._domain = domain
        self._project = project
        self._version = version
        self._client: Any = None

    @property
    def client(self) -> Any:
        if self._client is None:
            self._client = _get_client()
        return self._client

    def _resolve_key(self, key: str) -> str:
        """Return full composite key; if key is short name, build full key with domain/project/version."""
        if self.parse_key(key) is not None:
            return key
        return self.build_key(
            name=key, project=self._project, domain=self._domain, version=self._version
        )

    def _secret_id(self, key: str) -> str:
        """GCP secret ID = sanitized full composite key (or key as-is if already from list)."""
        full = self._resolve_key(key)
        # If key was from list_keys it may be already sanitized (underscores, no --)
        if full == key and "--" not in key and key.startswith("envr"):
            return key
        return _sanitize_secret_id(full)

    def _secret_name(self, secret_id: str) -> str:
        return f"projects/{self._project_id}/secrets/{secret_id}"

    def get(self, key: str) -> str | None:
        secret_id = self._secret_id(key)
        name = self._secret_name(secret_id)
        try:
            response = self.client.access_secret_version(
                request={"name": f"{name}/versions/latest"}
            )
            return response.payload.data.decode("utf-8")
        except Exception as e:
            if "NOT_FOUND" in str(e) or "404" in str(e):
                return None
            raise

    def set(self, key: str, value: str) -> None:
        secret_id = self._secret_id(key)
        parent = f"projects/{self._project_id}"
        full_name = self._secret_name(secret_id)
        try:
            self.client.get_secret(request={"name": full_name})
        except Exception as e:
            if "NOT_FOUND" in str(e) or "404" in str(e):
                from google.cloud import secretmanager  # type: ignore[import-untyped]
                self.client.create_secret(
                    request={
                        "parent": parent,
                        "secret_id": secret_id,
                        "secret": secretmanager.Secret(
                            replication=secretmanager.Replication(
                                automatic=secretmanager.Replication.Automatic()
                            )
                        ),
                    }
                )
            else:
                raise
        self.client.add_secret_version(
            request={
                "parent": full_name,
                "payload": {"data": value.encode("utf-8")},
            }
        )

    def delete(self, key: str) -> None:
        secret_id = self._secret_id(key)
        name = self._secret_name(secret_id)
        try:
            self.client.delete_secret(request={"name": name})
        except Exception as e:
            if "NOT_FOUND" in str(e) or "404" in str(e):
                pass
            else:
                raise

    def list_keys(self) -> list[str]:
        """Return keys (sanitized full composite or secret_id) so get(key) works."""
        prefix_full = f"projects/{self._project_id}/secrets/"
        filter_prefix = _sanitize_secret_id(self._path_prefix.rstrip("-"))
        keys: list[str] = []
        for secret in self.client.list_secrets(
            request={"parent": f"projects/{self._project_id}"}
        ):
            name = getattr(secret, "name", "") or ""
            if name.startswith(prefix_full):
                secret_id = name.split("/")[-1]
                if filter_prefix and secret_id.startswith(filter_prefix):
                    keys.append(secret_id)
                elif not filter_prefix and secret_id.startswith("envr"):
                    keys.append(secret_id)
        return sorted(set(keys))
