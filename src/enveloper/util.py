"""Shared utilities."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from enveloper.store import SecretStore


def strip_domain_prefix(key: str) -> str:
    """Strip domain/project prefix from a key name for use in local environment variables.

    When loading from a cloud store, keys may be stored with a path prefix (e.g.
    ``prod/API_KEY`` or ``myproject/prod/DATABASE_URL``). This returns the part
    after the last ``/`` so local env vars get clean names (e.g. ``API_KEY``).
    If there is no ``/``, the key is returned unchanged.
    """
    if "/" in key:
        return key.rsplit("/", 1)[-1]
    return key


def key_to_export_name(store: SecretStore, key: str) -> str:
    """Return the key name for export to a local file (prefix and version stripped).

    Use when exporting to .env or similar so output has plain names like API_KEY
    rather than envr/domain/proj/1.0.0/API_KEY.
    """
    return store.key_to_export_name(key)
