"""Shared utilities."""

from __future__ import annotations


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
