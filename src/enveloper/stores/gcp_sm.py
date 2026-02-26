"""GcpSmStore -- push/pull secrets to Google Cloud Secret Manager.

Requires ``google-cloud-secret-manager`` (install with ``pip install enveloper[gcp]``).
Uses Application Default Credentials or GOOGLE_APPLICATION_CREDENTIALS.
"""

from __future__ import annotations

import re
from typing import Any

from enveloper.store import SecretStore

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

    Each key is stored as a separate secret; secret ID = prefix + sanitized key.
    Uses Application Default Credentials (ADC) or GOOGLE_APPLICATION_CREDENTIALS.
    """

    def __init__(
        self,
        project_id: str,
        prefix: str = "enveloper-",
    ) -> None:
        self._project_id = project_id
        self._prefix = prefix.strip("_").rstrip("-")
        if self._prefix:
            self._prefix = self._prefix + "-"
        self._client: Any = None

    @property
    def client(self) -> Any:
        if self._client is None:
            self._client = _get_client()
        return self._client

    def _secret_id(self, key: str) -> str:
        return self._prefix + _sanitize_secret_id(key)

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
        prefix_full = f"projects/{self._project_id}/secrets/{self._prefix}"
        keys: list[str] = []
        for secret in self.client.list_secrets(
            request={"parent": f"projects/{self._project_id}"}
        ):
            name = getattr(secret, "name", "") or ""
            if name.startswith(prefix_full):
                # name is projects/PID/secrets/SECRET_ID
                secret_id = name.split("/")[-1]
                if secret_id.startswith(self._prefix):
                    key = secret_id[len(self._prefix) :]
                    keys.append(key)
        return sorted(set(keys))

    def clear(self) -> None:
        for key in self.list_keys():
            self.delete(key)
