"""Abstract base class for secret stores and plugin API for cloud stores."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar

# Default namespace used when project/domain are not provided (reserved name).
# Cloud store plugins may override via class attribute ``default_namespace``.
DEFAULT_NAMESPACE: str = "_default_"


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
    """

    # Optional: cloud stores set this to their preferred default when project/domain missing.
    default_namespace: ClassVar[str] = DEFAULT_NAMESPACE

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
