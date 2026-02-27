"""Tests for store plugin registry."""

from __future__ import annotations

import pytest

from enveloper.store import SecretStore
from enveloper.stores import get_service_entries, get_store_class, list_store_names
from enveloper.stores.keychain import KeychainStore


def test_get_service_entries_order_and_content():
    """get_service_entries yields keychain and file first, then others; each store has metadata."""
    entries = list(get_service_entries())
    names = [name for name, _ in entries]
    assert names[0] == "keychain"
    assert names[1] == "file"
    # keychain not repeated in plugin list
    assert names.count("keychain") == 1
    for name, store_cls in entries:
        assert issubclass(store_cls, SecretStore), f"{name} is not a SecretStore"
        rows = store_cls.get_service_rows()
        assert len(rows) >= 1, f"{name} must return at least one service row"
        for short_name, display_name, doc_url in rows:
            assert short_name, f"{name} row has empty short_name"
            assert display_name, f"{name} row has empty display_name"


def test_keychain_get_service_rows_returns_three_platforms():
    """KeychainStore reports three platform rows for local (MacOS/Windows/Linux)."""
    rows = KeychainStore.get_service_rows()
    assert len(rows) == 3
    short_names = [r[0] for r in rows]
    assert "local (MacOS)" in short_names
    assert "local (Windows)" in short_names
    assert "local (Linux)" in short_names
    assert all(r[2] for r in rows), "each platform row should have a doc URL"


def test_each_store_has_service_metadata():
    """Every store class used in get_service_entries has non-empty service_name and display name."""
    for _name, store_cls in get_service_entries():
        for short_name, display_name, _doc_url in store_cls.get_service_rows():
            assert short_name, f"{store_cls.__name__}: short_name must be set"
            assert display_name, f"{store_cls.__name__}: display_name must be set"


def test_list_store_names():
    names = list_store_names()
    assert "keychain" in names
    assert "aws" in names
    assert "github" in names


def test_get_keychain_store_class():
    cls = get_store_class("keychain")
    assert cls is KeychainStore


def test_get_unknown_store_raises():
    with pytest.raises(KeyError, match="Unknown store"):
        get_store_class("nonexistent-store")
