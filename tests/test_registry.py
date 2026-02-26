"""Tests for store plugin registry."""

from __future__ import annotations

import pytest

from enveloper.stores import get_store_class, list_store_names
from enveloper.stores.keychain import KeychainStore


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
