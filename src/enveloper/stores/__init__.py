# Copyright (c) 2026 Ramin Firoozye
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Store plugin registry -- discovers backends via ``enveloper.stores`` entry-point group."""

from __future__ import annotations

import sys
from collections.abc import Iterator

from enveloper.store import SecretStore
from enveloper.stores.file_store import FileStore
from enveloper.stores.keychain import KeychainStore

if sys.version_info >= (3, 12):
    from importlib.metadata import entry_points
else:
    from importlib.metadata import entry_points


def get_service_entries() -> Iterator[tuple[str, type[SecretStore]]]:
    """Yield (entry_name, store_class) in display order for ``enveloper service``.

    Order: keychain (local), file, then all other registered stores alphabetically.
    """
    yield "keychain", KeychainStore
    yield "file", FileStore
    for name in sorted(list_store_names()):
        if name != "keychain":
            yield name, get_store_class(name)


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
