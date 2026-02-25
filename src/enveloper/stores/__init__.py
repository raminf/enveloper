"""Store plugin registry -- discovers backends via ``enveloper.stores`` entry-point group."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from enveloper.store import SecretStore

if sys.version_info >= (3, 12):
    from importlib.metadata import entry_points
else:
    from importlib.metadata import entry_points


def get_store_class(name: str) -> type[SecretStore]:
    """Load a store class by its registered entry-point name.

    Raises ``KeyError`` with a helpful message when the name is unknown.
    """
    eps = entry_points(group="enveloper.stores")
    for ep in eps:
        if ep.name == name:
            return ep.load()

    available = sorted(ep.name for ep in eps)
    raise KeyError(
        f"Unknown store {name!r}. Available stores: {', '.join(available) or '(none)'}"
    )


def list_store_names() -> list[str]:
    """Return sorted names of all registered store plugins."""
    eps = entry_points(group="enveloper.stores")
    return sorted(ep.name for ep in eps)
