"""Tests for KeychainStore with mocked keyring backend."""

from __future__ import annotations

from enveloper.stores.keychain import KeychainStore


def test_set_and_get(mock_keyring):
    store = KeychainStore(project="test", domain="aws")
    store.set("MY_KEY", "my_value")
    assert store.get("MY_KEY") == "my_value"


def test_get_missing_returns_none(mock_keyring):
    store = KeychainStore(project="test", domain="aws")
    assert store.get("NONEXISTENT") is None


def test_delete(mock_keyring):
    store = KeychainStore(project="test", domain="aws")
    store.set("MY_KEY", "val")
    store.delete("MY_KEY")
    assert store.get("MY_KEY") is None


def test_delete_nonexistent_no_error(mock_keyring):
    store = KeychainStore(project="test", domain="aws")
    store.delete("NOPE")


def test_list_keys(mock_keyring):
    store = KeychainStore(project="test", domain="aws")
    store.set("B_KEY", "b")
    store.set("A_KEY", "a")
    assert sorted(store.list_keys()) == ["A_KEY", "B_KEY"]


def test_list_keys_empty(mock_keyring):
    store = KeychainStore(project="test", domain="aws")
    assert store.list_keys() == []


def test_clear(mock_keyring):
    store = KeychainStore(project="test", domain="aws")
    store.set("K1", "v1")
    store.set("K2", "v2")
    store.clear()
    assert store.list_keys() == []
    assert store.get("K1") is None
    assert store.get("K2") is None


def test_domain_isolation(mock_keyring):
    aws_store = KeychainStore(project="test", domain="aws")
    web_store = KeychainStore(project="test", domain="webdash")
    aws_store.set("KEY", "aws_val")
    web_store.set("KEY", "web_val")
    assert aws_store.get("KEY") == "aws_val"
    assert web_store.get("KEY") == "web_val"


def test_project_isolation(mock_keyring):
    store_a = KeychainStore(project="proj_a", domain="d")
    store_b = KeychainStore(project="proj_b", domain="d")
    store_a.set("KEY", "a")
    store_b.set("KEY", "b")
    assert store_a.get("KEY") == "a"
    assert store_b.get("KEY") == "b"


def test_set_with_domain_tracking(mock_keyring):
    store = KeychainStore(project="test", domain="aws")
    store.set_with_domain_tracking("MY_KEY", "val")
    global_store = KeychainStore(project="test")
    assert "aws" in global_store.list_domains()


def test_manifest_consistency_after_set_delete(mock_keyring):
    store = KeychainStore(project="test", domain="aws")
    store.set("A", "1")
    store.set("B", "2")
    assert sorted(store.list_keys()) == ["A", "B"]
    store.delete("A")
    assert store.list_keys() == ["B"]
