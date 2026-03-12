# Copyright (c) 2026 Ramin Firoozye
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Abstract base class for secret stores and plugin API for cloud stores."""

from __future__ import annotations

import base64
import json
import re
import zlib
from abc import ABC, abstractmethod
from typing import TypeVar

from enveloper.security import (
    sanitize_namespace_segment,
    sanitize_secret_key,
    sanitize_secret_pair,
    sanitize_secret_value,
)

# Default namespace used when project/domain are not provided (reserved name).
# Cloud store plugins may override via class attribute ``default_namespace``.
DEFAULT_NAMESPACE: str = "_default_"

# Default version (semver format)
DEFAULT_VERSION: str = "1.0.0"

# Default prefix for cloud stores
DEFAULT_PREFIX: str = "envr"

# Regex pattern for valid semver version
_SEMVER_PATTERN = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
    r"(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
)


def is_valid_semver(version: str) -> bool:
    """Check if a version string is valid semver format."""
    return bool(_SEMVER_PATTERN.match(version))


SecretStoreT = TypeVar("SecretStoreT", bound="SecretStore")


class SecretStore(ABC):
    """Backend for reading/writing secrets.

    Implementations must handle their own authentication and connection
    lifecycle.  Write-only stores (e.g. GitHub Secrets) should raise
    ``NotImplementedError`` from :meth:`get`.

    All stores must implement :meth:`clear`; it is used when the user runs
    ``enveloper clear --service <name>`` to remove every key from that backend.

    **Plugin API for cloud stores** (optional): to control how keys are
    namespaced when no explicit prefix is provided, a store class may define:

    - ``default_namespace`` (class attribute, str): value used when
      project or domain are missing (e.g. ``"_default_"``). Enables using
      ``"default"`` as a user-chosen project/domain name without conflict.

    - ``build_default_prefix(domain: str, project: str) -> str`` (class method):
      returns the default prefix or path for this store, including the given
      domain and project (already resolved with default_namespace). The store
      can use its own separator and sanitization (e.g. ``/`` for AWS, ``--``
      for GCP, ``__`` for GitHub). Used by :mod:`enveloper.resolve_store` when
      instantiating the store with ``prefix=None``.

    - ``version_separator`` (class attribute, str): separator to use for version
      in keys. Use "." for most stores, "_" for stores that don't support dots
      in keys (e.g. GitHub Secrets). Default is ".".

    - ``key_separator`` (class attribute, str): separator to use for path
      segments in keys. Use "/" for AWS, "--" for GCP/Azure, "__" for GitHub.
      Default is "/". The sanitize_key_segment method ensures this character
      is not present in name, domain, or project values.

    **Service listing** (for ``enveloper service``): each store must define
    ``service_name`` (short CLI name, e.g. ``"aws"``), ``service_display_name``
    (human-readable description), and ``service_doc_url`` (documentation link).
    Override :meth:`get_service_rows` only if the store contributes multiple
    rows (e.g. local keychain per platform).

    **Configuration API**: stores can override :meth:`from_config` to customize
    how they are instantiated from configuration. This allows each store to
    encapsulate its own configuration resolution logic.
    """

    # Optional: cloud stores set this to their preferred default when project/domain missing.
    default_namespace: str = DEFAULT_NAMESPACE

    # Version separator: "." for most stores, "_" for stores that don't support dots
    version_separator: str = "."

    # Key separator: "/" for AWS, "--" for GCP/Azure, "__" for GitHub
    # This is used to separate path segments in keys
    key_separator: str = "/"

    # Prefix for cloud stores (default: "envr")
    prefix: str = DEFAULT_PREFIX

    # Service listing (enveloper service): short name, display name, doc link
    service_name: str = ""
    service_display_name: str = ""
    service_doc_url: str = ""

    def __init__(self, *args: object, **kwargs: object) -> None:
        """Subclasses override with their own constructor signatures."""
        pass

    @classmethod
    def build_default_prefix(cls, domain: str, project: str) -> str:
        """Default prefix/path for this store. Override in subclasses."""
        d = cls.sanitize_key_segment(domain)
        p = cls.sanitize_key_segment(project)
        return f"{cls.prefix}{cls.key_separator}{d}{cls.key_separator}{p}{cls.key_separator}"

    @classmethod
    def get_service_rows(cls) -> list[tuple[str, str, str]]:
        """Return one or more (short_name, display_name, doc_url) for the service table.

        Default: one row from service_name, service_display_name, service_doc_url.
        Override to return multiple rows (e.g. KeychainStore for each OS platform).
        """
        return [(cls.service_name, cls.service_display_name, cls.service_doc_url)]

    @abstractmethod
    def get(self, key: str) -> str | None:
        """Return the value for *key*, or ``None`` if it does not exist."""

    @abstractmethod
    def set(self, key: str, value: str) -> None:
        """Create or overwrite *key* with *value*."""

    @abstractmethod
    def delete(self, key: str) -> None:
        """Remove the entire key/secret from the store.

        The key must no longer appear in :meth:`list_keys` and :meth:`get`
        must return ``None`` for it. No error if the key does not exist.
        """

    @abstractmethod
    def list_keys(self) -> list[str]:
        """Return all key names managed by this store."""

    # ------------------------------------------------------------------
    # Metadata registry (domain/project tracking via compressed keys)
    # ------------------------------------------------------------------

    def _get_meta_domains_key(self) -> str:
        """Return the metadata key for the list of domains. Override in subclasses for service-specific naming."""
        return "_envr_meta_domains_"

    def _get_meta_projects_key(self, domain: str) -> str:
        """Return the metadata key for the list of projects in a domain. Override in subclasses for service-specific naming."""
        safe = self.sanitize_key_segment(domain)
        return f"_envr_meta_dom_{safe}_projects_"

    @staticmethod
    def _compress(data: str) -> str:
        return base64.b64encode(zlib.compress(data.encode())).decode("ascii")

    @staticmethod
    def _decompress(data: str) -> str:
        return zlib.decompress(base64.b64decode(data)).decode()

    def _raw_get(self, key: str) -> str | None:
        """Read a raw metadata key. Subclasses override to bypass key building."""
        return self.get(key)

    def _raw_set(self, key: str, value: str) -> None:
        """Write a raw metadata key. Subclasses override to bypass key building."""
        self.set(key, value)

    def _raw_delete(self, key: str) -> None:
        """Delete a raw metadata key. Subclasses override to bypass key building."""
        self.delete(key)

    def _read_meta_list(self, meta_key: str) -> list[str]:
        raw = self._raw_get(meta_key)
        if raw is None:
            return []
        try:
            return json.loads(self._decompress(raw))
        except Exception:
            return []

    def _write_meta_list(self, meta_key: str, items: list[str]) -> None:
        self._raw_set(meta_key, self._compress(json.dumps(sorted(set(items)))))

    def register_domain(self, domain: str) -> None:
        meta_key = self._get_meta_domains_key()
        domains = self._read_meta_list(meta_key)
        if domain not in domains:
            domains.append(domain)
            self._write_meta_list(meta_key, domains)

    def unregister_domain(self, domain: str) -> None:
        meta_key = self._get_meta_domains_key()
        domains = self._read_meta_list(meta_key)
        if domain not in domains:
            return
        domains = [d for d in domains if d != domain]
        if domains:
            self._write_meta_list(meta_key, domains)
        else:
            self._raw_delete(meta_key)
        self._raw_delete(self._get_meta_projects_key(domain))

    def register_project(self, domain: str, project: str) -> None:
        key = self._get_meta_projects_key(domain)
        projects = self._read_meta_list(key)
        if project not in projects:
            projects.append(project)
            self._write_meta_list(key, projects)

    def unregister_project(self, domain: str, project: str) -> None:
        meta_key = self._get_meta_projects_key(domain)
        projects = self._read_meta_list(meta_key)
        if project not in projects:
            return
        projects = [p for p in projects if p != project]
        if projects:
            self._write_meta_list(meta_key, projects)
        else:
            self._raw_delete(meta_key)
            self.unregister_domain(domain)

    def set_with_tracking(self, key: str, value: str) -> None:
        """Set a key and update the domain/project metadata registry."""
        if self.parse_key(key) is None:
            key, value = sanitize_secret_pair(key, value)
        else:
            value = sanitize_secret_value(value)
        self.set(key, value)
        domain = getattr(self, "_domain", None) or DEFAULT_NAMESPACE
        project = getattr(self, "_project", None) or DEFAULT_NAMESPACE
        self.register_domain(domain)
        self.register_project(domain, project)

    def delete_with_tracking(self, key: str) -> None:
        """Delete a key and update the metadata registry if the project/domain is now empty."""
        if self.parse_key(key) is None:
            key = sanitize_secret_key(key)
        self.delete(key)
        domain = getattr(self, "_domain", None) or DEFAULT_NAMESPACE
        project = getattr(self, "_project", None) or DEFAULT_NAMESPACE
        remaining = [k for k in self.list_keys() if k != key]
        has_project = False
        for k in remaining:
            parsed = self.parse_key(k)
            if parsed and parsed.get("domain") == domain and parsed.get("project") == project:
                has_project = True
                break
        if not has_project:
            self.unregister_project(domain, project)

    def list_domains(self) -> list[str]:
        """Return domain names. Reads metadata registry first, falls back to key scan."""
        meta_key = self._get_meta_domains_key()
        cached = self._read_meta_list(meta_key)
        if cached:
            return sorted(cached)
        domains = set()
        for key in self.list_keys():
            parsed = self.parse_key(key)
            if parsed and parsed.get("domain"):
                domains.add(parsed["domain"])
        result = sorted(domains)
        if result:
            self._write_meta_list(meta_key, result)
        return result

    def list_projects(self, domain: str) -> list[str]:
        """Return project names for a domain. Reads metadata first, falls back to key scan."""
        meta_key = self._get_meta_projects_key(domain)
        cached = self._read_meta_list(meta_key)
        if cached:
            return sorted(cached)
        projects = set()
        for key in self.list_keys():
            parsed = self.parse_key(key)
            if parsed and parsed.get("domain") == domain and parsed.get("project"):
                projects.add(parsed["project"])
        result = sorted(projects)
        if result:
            self._write_meta_list(meta_key, result)
        return result

    def rebuild_registry(self) -> dict[str, list[str]]:
        """Scan all keys and rebuild domain/project metadata from scratch.

        Returns a mapping of domain -> [projects].
        """
        domain_projects: dict[str, set[str]] = {}
        for key in self.list_keys():
            parsed = self.parse_key(key)
            if parsed:
                d = parsed.get("domain")
                p = parsed.get("project")
                if d:
                    domain_projects.setdefault(d, set())
                    if p:
                        domain_projects[d].add(p)
        result: dict[str, list[str]] = {}
        domains = sorted(domain_projects.keys())
        meta_domains_key = self._get_meta_domains_key()
        if domains:
            self._write_meta_list(meta_domains_key, domains)
        for d in domains:
            projects = sorted(domain_projects[d])
            if projects:
                self._write_meta_list(self._get_meta_projects_key(d), projects)
            result[d] = projects
        return result

    def clear_metadata(self) -> None:
        """Delete all metadata registry keys."""
        meta_domains_key = self._get_meta_domains_key()
        domains = self._read_meta_list(meta_domains_key)
        for d in domains:
            try:
                self._raw_delete(self._get_meta_projects_key(d))
            except Exception:
                pass
        try:
            self._raw_delete(meta_domains_key)
        except Exception:
            pass

    def clear(self) -> None:
        """Remove every key managed by this store (default: delete each key from list_keys).

        Used by the CLI when the user runs ``enveloper clear --service <name>``.
        Subclasses may override for a more efficient bulk clear.
        """
        for key in self.list_keys():
            self.delete(key)

    def _get_prefix(self) -> str:
        """Get the prefix for this store instance."""
        return getattr(self, "prefix", DEFAULT_PREFIX)

    @classmethod
    def sanitize_key_segment(cls, value: str) -> str:
        """Sanitize a key segment (name, domain, or project) to ensure it doesn't contain the key separator.

        This method is called by build_key and build_default_prefix to ensure
        that keys can be properly parsed later. The key_separator character
        is replaced with an underscore.

        Parameters
        ----------
        value : str
            The value to sanitize (name, domain, or project).

        Returns
        -------
        str
            The sanitized value with key_separator replaced by underscore.
        """
        safe_value = sanitize_namespace_segment(
            value,
            default=cls.default_namespace,
            field_name="key segment",
        )
        sanitized = safe_value.replace(cls.key_separator, "_")
        sanitized = sanitized.replace("\\", "_")
        return sanitized.strip() or cls.default_namespace

    @staticmethod
    def sanitize_secret_key(key: str) -> str:
        """Validate and normalize a secret key."""
        return sanitize_secret_key(key)

    @staticmethod
    def sanitize_secret_value(value: str, *, key: str | None = None) -> str:
        """Validate a secret value."""
        return sanitize_secret_value(value, key=key)

    def build_key(self, name: str, domain: str, project: str, version: str = DEFAULT_VERSION) -> str:
        """Build a key with prefix, domain, project, version, and name components.

        The key format is: {prefix}{key_separator}{domain}{key_separator}{project}{key_separator}{version}{key_separator}{name}

        Domain always comes before project. The version separator is determined by the
        store class (default "."). The key separator is used to separate path segments.

        This method sanitizes name, domain, and project to ensure the key_separator
        character is not present in any of them.
        """
        # Sanitize all segments to prevent key_separator in names
        name_safe = self.sanitize_secret_key(name)
        domain_safe = self.sanitize_key_segment(domain)
        project_safe = self.sanitize_key_segment(project)

        sep = self.version_separator
        version_safe = version.replace(".", sep)
        prefix = self._get_prefix()
        return (
            f"{prefix}{self.key_separator}{domain_safe}{self.key_separator}"
            f"{project_safe}{self.key_separator}{version_safe}{self.key_separator}{name_safe}"
        )

    def parse_key(self, key: str) -> dict[str, str] | None:
        """Parse a key and return its components.

        Returns a dict with keys: prefix, project, domain, version, name.
        Returns None if the key doesn't match the expected format.
        Keys may have a leading separator (e.g. /envr/domain/proj/1.0.0/name);
        leading/trailing separators are stripped before parsing.
        """
        sep = self.key_separator
        # Strip leading/trailing separator so "/envr/domain/proj/1.0.0/name" parses correctly
        stripped = key.strip(sep) if sep else key
        if not stripped:
            return None
        parts = stripped.split(sep)
        if len(parts) < 5:
            return None

        # Order: prefix, domain, project, version, name (last five segments)
        try:
            name = parts[-1]
            version = parts[-2]
            project = parts[-3]
            domain = parts[-4]
            prefix = parts[-5]

            # Convert version separator back to dots for storage
            version_normalized = version.replace("_", ".")

            return {
                "prefix": prefix,
                "project": project,
                "domain": domain,
                "version": version_normalized,
                "name": name,
            }
        except (IndexError, ValueError):
            return None

    def key_to_export_name(self, key: str) -> str:
        """Return the key name for export to a local file (prefix and version stripped).

        When exporting to a .env or similar file, use this so output has plain
        names like API_KEY rather than envr/domain/proj/1.0.0/API_KEY.
        """
        parsed = self.parse_key(key)
        if parsed:
            return parsed["name"]
        # Fallback: strip by separator (e.g. last segment after /)
        if self.key_separator in key:
            return key.rsplit(self.key_separator, 1)[-1]
        return key

    @classmethod
    def from_config(
        cls: type[SecretStoreT],
        domain: str,
        project: str,
        config: object,
        prefix: str | None = None,
        env_name: str | None = None,
        **kwargs: object,
    ) -> SecretStoreT:
        """Create a store instance from configuration.

        This is a default implementation that subclasses can override to customize
        how they resolve their configuration. The base implementation uses the
        store's plugin API to build the default prefix.

        Parameters
        ----------
        domain : str
            Domain / subsystem scope.
        project : str
            Project namespace.
        config : object
            Configuration object (EnveloperConfig) with store-specific settings.
        prefix : str, optional
            Explicit prefix/path for the store. If None, uses build_default_prefix.
        env_name : str, optional
            Environment name for resolving {env} in config.
        **kwargs : object
            Additional keyword arguments passed to the store constructor.

        Returns
        -------
        SecretStore
            An instantiated store with resolved configuration.
        """
        # Use explicit prefix if provided, otherwise use the store's default
        if prefix is None:
            prefix = cls.build_default_prefix(domain, project)

        # Create store with resolved prefix, domain, project, and any additional kwargs
        return cls(prefix=prefix, domain=domain, project=project, **kwargs)
