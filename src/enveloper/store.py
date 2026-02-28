# Copyright (c) 2026 Ramin Firoozye
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Abstract base class for secret stores and plugin API for cloud stores."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import ClassVar

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
    default_namespace: ClassVar[str] = DEFAULT_NAMESPACE

    # Version separator: "." for most stores, "_" for stores that don't support dots
    version_separator: ClassVar[str] = "."

    # Key separator: "/" for AWS, "--" for GCP/Azure, "__" for GitHub
    # This is used to separate path segments in keys
    key_separator: ClassVar[str] = "/"

    # Prefix for cloud stores (default: "envr")
    prefix: ClassVar[str] = DEFAULT_PREFIX

    # Service listing (enveloper service): short name, display name, doc link
    service_name: ClassVar[str] = ""
    service_display_name: ClassVar[str] = ""
    service_doc_url: ClassVar[str] = ""

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
        if not value or not value.strip():
            return cls.default_namespace
        # Replace the key_separator with underscore
        sanitized = value.replace(cls.key_separator, "_")
        # Also replace common path separators that could cause issues
        sanitized = sanitized.replace("\\", "_")
        return sanitized.strip() or cls.default_namespace

    def build_key(self, name: str, project: str, domain: str, version: str = DEFAULT_VERSION) -> str:
        """Build a key with project, domain, version, and name components.

        The key format is: {prefix}{key_separator}{domain}{key_separator}{project}{key_separator}{version}{key_separator}{name}

        The version separator is determined by the store class (default ".").
        The key separator is used to separate path segments.

        This method sanitizes name, domain, and project to ensure the key_separator
        character is not present in any of them.
        """
        # Sanitize all segments to prevent key_separator in names
        name_safe = self.sanitize_key_segment(name)
        project_safe = self.sanitize_key_segment(project)
        domain_safe = self.sanitize_key_segment(domain)

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
        cls,
        domain: str,
        project: str,
        config: object,
        prefix: str | None = None,
        env_name: str | None = None,
        **kwargs: object,
    ) -> SecretStore:
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

