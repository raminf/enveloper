# Copyright (c) 2026 Ramin Firoozye
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Unit tests for VaultStore (HashiCorp Vault KV v2).

Uses mocked hvac client; no real Vault server required. For integration tests
against a real Vault (local Docker or HCP Vault Dedicated), see
tests/integration/test_vault.py.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from enveloper.security import SanitizationError
from enveloper.store import DEFAULT_PREFIX
from enveloper.stores.vault import VaultStore


def test_vault_build_default_prefix():
    """VaultStore uses envr/domain/project path."""
    assert VaultStore.build_default_prefix("dev", "myapp") == f"{DEFAULT_PREFIX}/dev/myapp"
    assert VaultStore.build_default_prefix("staging", "svc") == f"{DEFAULT_PREFIX}/staging/svc"
    with pytest.raises(SanitizationError):
        VaultStore.sanitize_key_segment("a/b")


@pytest.fixture
def mock_vault_client():
    """Mock hvac client with KV v2 read/write responses."""
    data: dict[str, str] = {}

    def read_secret_version(path=None, mount_point=None):
        return {"data": {"data": dict(data)}}

    def create_or_update_secret(path=None, secret=None, mount_point=None):
        data.clear()
        data.update(secret or {})

    client = MagicMock()
    client.secrets.kv.v2.read_secret_version.side_effect = read_secret_version
    client.secrets.kv.v2.create_or_update_secret.side_effect = create_or_update_secret
    client.is_authenticated.return_value = True
    return client


@patch("enveloper.stores.vault._get_client")
def test_vault_store_set_get_list_delete(mock_get_client, mock_vault_client):
    """VaultStore set, get, list_keys, delete with composite keys."""
    mock_get_client.return_value = mock_vault_client
    store = VaultStore(
        path="envr/dev/myapp",
        mount_point="secret",
        url="http://127.0.0.1:8200",
        token="root",
        domain="dev",
        project="myapp",
        version="1.0.0",
    )

    # set and get by short name
    store.set("API_KEY", "secret123")
    assert store.get("API_KEY") == "secret123"
    assert store.list_keys() == [store.build_key("API_KEY", "dev", "myapp", "1.0.0")]

    # set another
    store.set("DB_URL", "postgres://localhost/db")
    keys = store.list_keys()
    assert len(keys) == 2
    assert store.get("DB_URL") == "postgres://localhost/db"

    # delete
    store.delete("API_KEY")
    assert store.get("API_KEY") is None
    assert store.get("DB_URL") == "postgres://localhost/db"
    assert len(store.list_keys()) == 1

    store.delete("DB_URL")
    assert store.get("DB_URL") is None
    assert store.list_keys() == []


@patch("enveloper.stores.vault._get_client")
def test_vault_store_clear(mock_get_client, mock_vault_client):
    """VaultStore clear writes empty dict to path."""
    mock_get_client.return_value = mock_vault_client
    store = VaultStore(
        path="envr/test/clear",
        mount_point="secret",
        domain="test",
        project="clear",
    )
    store.set("X", "1")
    store.set("Y", "2")
    assert len(store.list_keys()) == 2
    store.clear()
    assert store.list_keys() == []
    mock_vault_client.secrets.kv.v2.create_or_update_secret.assert_called()
    call_kw = mock_vault_client.secrets.kv.v2.create_or_update_secret.call_args
    assert call_kw[1]["secret"] == {}


@patch("enveloper.stores.vault._get_client")
def test_vault_store_read_empty_path(mock_get_client):
    """VaultStore _read_data returns {} when path not found (404)."""
    # Use hvac.exceptions.InvalidPath when available; otherwise Exception("not found")
    # so _vault_path_not_found works with or without enveloper[vault] (e.g. CI).
    try:
        import hvac.exceptions
        path_error = hvac.exceptions.InvalidPath()
    except ImportError:
        path_error = Exception("path not found")

    client = MagicMock()
    client.is_authenticated.return_value = True
    client.secrets.kv.v2.read_secret_version.side_effect = path_error

    mock_get_client.return_value = client

    store = VaultStore(path="envr/nonexistent/proj", mount_point="secret")
    assert store.list_keys() == []
    assert store.get("ANY_KEY") is None


@patch("enveloper.stores.vault._get_client")
def test_vault_store_from_config(mock_get_client, mock_vault_client):
    """VaultStore.from_config uses url and mount_point from kwargs (as resolve_store passes)."""
    mock_get_client.return_value = mock_vault_client
    store = VaultStore.from_config(
        domain="prod",
        project="api",
        config=MagicMock(),
        prefix=f"{DEFAULT_PREFIX}/prod/api",
        url="https://vault.example.com",
        mount_point="my-mount",
    )
    assert store._path == "envr/prod/api"
    assert store._mount_point == "my-mount"
    assert store._url == "https://vault.example.com"
    store.set("K", "v")
    assert store.get("K") == "v"
    mock_get_client.assert_called_once_with("https://vault.example.com", None)
