"""Abstract base class for secret stores."""

from __future__ import annotations

from abc import ABC, abstractmethod


class SecretStore(ABC):
    """Backend for reading/writing secrets.

    Implementations must handle their own authentication and connection
    lifecycle.  Write-only stores (e.g. GitHub Secrets) should raise
    ``NotImplementedError`` from :meth:`get`.

    All stores must implement :meth:`clear`; it is used when the user runs
    ``enveloper clear --service <name>`` to remove every key from that backend.
    """

    @abstractmethod
    def get(self, key: str) -> str | None:
        """Return the value for *key*, or ``None`` if it does not exist."""

    @abstractmethod
    def set(self, key: str, value: str) -> None:
        """Create or overwrite *key* with *value*."""

    @abstractmethod
    def delete(self, key: str) -> None:
        """Remove *key*.  No error if the key does not exist."""

    @abstractmethod
    def list_keys(self) -> list[str]:
        """Return all key names managed by this store."""

    @abstractmethod
    def clear(self) -> None:
        """Remove every key managed by this store.

        Used by the CLI when the user runs ``enveloper clear --service <name>``.
        """
