# Copyright (c) 2026 Ramin Firoozye
# SPDX-License-Identifier: AGPL-3.0-or-later

"""GcpSmStore -- push/pull secrets to Google Cloud Secret Manager.

Requires ``google-cloud-secret-manager`` (install with ``pip install enveloper[gcp]``).
Uses Application Default Credentials or GOOGLE_APPLICATION_CREDENTIALS.
"""

from __future__ import annotations

import os
import re
import subprocess
from typing import Any

from enveloper.security import sanitize_namespace_segment, sanitize_secret_key, sanitize_secret_pair
from enveloper.store import DEFAULT_NAMESPACE, DEFAULT_PREFIX, DEFAULT_VERSION, SecretStore

# GCP project ID: 6-30 lowercase chars, starts with letter, ends with alphanumeric, can include hyphens
_GCP_PROJECT_ID_RE = re.compile(r"^[a-z][a-z0-9-]{4,28}[a-z0-9]$")

# GCP project number (numeric ID)
_GCP_PROJECT_NUMBER_RE = re.compile(r"^[0-9]+$")

_MISSING_GCP = (
    "google-cloud-secret-manager is required for the gcp store. "
    "Install it with: pip install enveloper[gcp]"
)

# GCP secret ID: 1-255 chars, [a-zA-Z0-9_-]+
_SECRET_ID_RE = re.compile(r"[^a-zA-Z0-9_-]+")


def _gcloud_default_project() -> str | None:
    """Return the active gcloud project ID (``gcloud config get-value project``)."""
    try:
        result = subprocess.run(
            ["gcloud", "config", "get-value", "project"],
            capture_output=True, text=True, timeout=5,
        )
        project = result.stdout.strip()
        if project and result.returncode == 0 and project != "(unset)":
            return project
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


def _gcloud_resolve_name(display_name: str) -> str | None:
    """Resolve a GCP project display name to project_id via ``gcloud projects list``."""
    try:
        result = subprocess.run(
            [
                "gcloud", "projects", "list",
                f"--filter=name={display_name}",
                "--format=value(projectId)",
            ],
            capture_output=True, text=True, timeout=10,
        )
        project_id = result.stdout.strip().split("\n")[0].strip()
        if project_id and result.returncode == 0:
            return project_id
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


def _resolve_name_via_api(display_name: str) -> str | None:
    """Resolve a GCP project display name to project_id via Resource Manager API."""
    try:
        from google.cloud import resourcemanager_v3  # type: ignore[import-untyped,attr-defined]
        client = resourcemanager_v3.ProjectsClient()
        for proj in client.search_projects(query=f"displayName={display_name}"):
            if proj.display_name == display_name:
                return proj.project_id
    except Exception:
        pass
    try:
        from google.cloud import resourcemanager  # type: ignore[import-untyped,attr-defined]
        client = resourcemanager.ProjectsClient()
        for proj in client.list_projects():
            if proj.display_name == display_name or proj.project_id == display_name:
                return proj.project_id
    except Exception:
        pass
    return None


def resolve_gcp_project_id(value: str) -> str:
    """Resolve a GCP project identifier to a concrete project_id.

    Accepts:
    - A valid project ID (e.g. ``my-project``) -- returned as-is.
    - A project number (e.g. ``123456789``) -- returned as-is.
    - A ``projects/...`` resource name -- the ID portion is extracted.
    - A human-friendly *display name* (e.g. ``"My Cool Project"``) -- resolved
      via the Resource Manager API, or falling back to ``gcloud projects list``.

    Raises ``ValueError`` if the name cannot be resolved.
    """
    if _GCP_PROJECT_ID_RE.match(value):
        return value
    if _GCP_PROJECT_NUMBER_RE.match(value):
        return value
    if value.startswith("projects/"):
        part = value.split("/", 1)[1]
        if _GCP_PROJECT_ID_RE.match(part) or _GCP_PROJECT_NUMBER_RE.match(part):
            return part

    # Treat as a display name and try to resolve
    resolved = _resolve_name_via_api(value) or _gcloud_resolve_name(value)
    if resolved:
        return resolved
    raise ValueError(
        f"Could not resolve GCP project name '{value}' to a project ID.\n"
        "Ensure the name matches the 'Project name' shown in the GCP console,\n"
        "or use the project ID directly (e.g. 'my-project-123456')."
    )


def _detect_gcp_project() -> str | None:
    """Detect the GCP project ID from environment variables or gcloud SDK.

    Resolution order:
    1. ENVELOPER_GCP_PROJECT
    2. GOOGLE_CLOUD_PROJECT (standard GCP SDK variable)
    3. GCLOUD_PROJECT (legacy)
    4. ``gcloud config get-value project`` (active gcloud configuration)

    Values that look like display names (not valid project IDs) are resolved
    to an actual project_id before returning.
    """
    for var in ("ENVELOPER_GCP_PROJECT", "GOOGLE_CLOUD_PROJECT", "GCLOUD_PROJECT"):
        val = os.environ.get(var, "").strip()
        if val:
            try:
                return resolve_gcp_project_id(val)
            except ValueError:
                return val
    return _gcloud_default_project()


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

    @classmethod
    def resolve_project_name(cls, project_name: str) -> str:
        """Resolve a GCP project name / display name / ID to a project_id.

        Delegates to the module-level :func:`resolve_gcp_project_id`.
        """
        return resolve_gcp_project_id(project_name)

    def __init__(
        self,
        project_id: str,
        prefix: str = "envr--",
        domain: str = DEFAULT_NAMESPACE,
        project: str = DEFAULT_NAMESPACE,
        version: str = DEFAULT_VERSION,
        **kwargs: object,
    ) -> None:
        # Validate project_id is not the default placeholder
        if project_id == "_default_":
            raise ValueError(
                "GCP project_id cannot be '_default_'. Please provide a valid GCP project ID "
                "(e.g., 'my-project' or 'projects/my-project')."
            )

        if not _GCP_PROJECT_ID_RE.match(project_id) and not _GCP_PROJECT_NUMBER_RE.match(project_id):
            raise ValueError(
                f"Invalid GCP project_id '{project_id}'. "
                "Project ID must be 6-30 lowercase characters, start with a letter, "
                "end with an alphanumeric character, and can include hyphens. "
                "You can also use a numeric project number, or set a display name "
                "in .enveloper.toml which will be resolved automatically."
            )

        self._project_id = project_id
        self._path_prefix = prefix
        self._domain = sanitize_namespace_segment(domain, default=DEFAULT_NAMESPACE, field_name="domain")
        self._project = sanitize_namespace_segment(project, default=DEFAULT_NAMESPACE, field_name="project")
        self._version = version
        self._client: Any = None

    @property
    def client(self) -> Any:
        if self._client is None:
            self._client = _get_client()
        return self._client

    def _raw_get(self, key: str) -> str | None:
        name = self._secret_name(key)
        try:
            response = self.client.access_secret_version(
                request={"name": f"{name}/versions/latest"}
            )
            return response.payload.data.decode("utf-8")
        except Exception as e:
            if "NOT_FOUND" in str(e) or "404" in str(e):
                return None
            raise

    def _raw_set(self, key: str, value: str) -> None:
        parent = f"projects/{self._project_id}"
        full_name = self._secret_name(key)
        try:
            self.client.get_secret(request={"name": full_name})
        except Exception as e:
            if "NOT_FOUND" in str(e) or "404" in str(e):
                from google.cloud import secretmanager  # type: ignore[import-untyped]
                self.client.create_secret(
                    request={
                        "parent": parent,
                        "secret_id": key,
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

    def _raw_delete(self, key: str) -> None:
        name = self._secret_name(key)
        try:
            self.client.delete_secret(request={"name": name})
        except Exception as e:
            if "NOT_FOUND" in str(e) or "404" in str(e):
                pass
            else:
                raise

    def _resolve_key(self, key: str) -> str:
        """Return full composite key; if key is short name, build full key with domain/project/version."""
        if self.parse_key(key) is not None:
            return key
        return self.build_key(
            name=key, domain=self._domain, project=self._project, version=self._version
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
        if self.parse_key(key) is None:
            key, value = sanitize_secret_pair(key, value)
        else:
            value = self.sanitize_secret_value(value)
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
        if self.parse_key(key) is None:
            key = sanitize_secret_key(key)
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
        filter_prefix = _sanitize_secret_id(self._path_prefix.rstrip("-"))
        keys: list[str] = []
        for secret in self.client.list_secrets(
            request={"parent": f"projects/{self._project_id}"}
        ):
            # GCP returns resource names using the numeric project number
            # (e.g. projects/123456/secrets/...) which may differ from the
            # project ID string, so extract secret_id by splitting on "/".
            name = getattr(secret, "name", "") or ""
            secret_id = name.rsplit("/", 1)[-1] if "/" in name else name
            if not secret_id:
                continue
            if filter_prefix and secret_id.startswith(filter_prefix):
                keys.append(secret_id)
            elif not filter_prefix and secret_id.startswith("envr"):
                keys.append(secret_id)
        return sorted(set(keys))

    @classmethod
    def from_config(
        cls: type["GcpSmStore"],
        domain: str,
        project: str,
        config: object,
        prefix: str | None = None,
        env_name: str | None = None,
        **kwargs: object,
    ) -> "GcpSmStore":
        """Create a GCP store from configuration, resolving project names to IDs.

        If the project is a human-friendly name (not a valid project ID),
        this method attempts to resolve it to a project ID using the GCP API.
        """
        # Get project_id from kwargs if provided, otherwise use project
        project_id = kwargs.get("project_id", project)
        project_id_str = project if project_id is None else str(project_id)

        # Resolve project name to project ID if needed
        resolved_project_id = cls.resolve_project_name(project_id_str)

        # Update kwargs with resolved project_id
        kwargs["project_id"] = resolved_project_id

        # Call parent from_config to create the store
        return super().from_config(
            domain=domain,
            project=project,
            config=config,
            prefix=prefix,
            env_name=env_name,
            **kwargs,
        )
