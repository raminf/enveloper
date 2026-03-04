"""Integration tests for Vault store (vault).

Works with any Vault server (local Docker, self-hosted, or HCP Vault Dedicated).
Disabled by default. To run:

  pip install enveloper[vault]
  export ENVELOPER_TEST_VAULT=1
  export VAULT_ADDR=http://127.0.0.1:8200
  export VAULT_TOKEN=root
  # Start local Vault first, e.g.: docker compose -f docker-compose.vault.yml up -d
  pytest -m integration_vault tests/integration/test_vault.py -v
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration_vault


def test_vault_set_get_delete_list(vault_credentials):
    """Set, get, list, and delete secrets in Vault KV v2."""
    from enveloper.stores.vault import VaultStore

    prefix = "envr/integration-test/vault1"
    store = VaultStore(
        path=prefix,
        mount_point="secret",
        url=vault_credentials["url"],
        token=vault_credentials["token"],
        domain="integration-test",
        project="vault1",
    )
    key = "ENVELOPER_TEST_KEY"
    value = "secret-value-for-vault-integration-test"

    try:
        store.set(key, value)
        assert store.get(key) == value
        assert any(key in k or "ENVELOPER_TEST_KEY" in k for k in store.list_keys())
    finally:
        store.delete(key)

    assert store.get(key) is None


def test_vault_clear(vault_credentials):
    """Clear all secrets at the test path."""
    from enveloper.stores.vault import VaultStore

    prefix = "envr/integration-test/vault-clear"
    store = VaultStore(
        path=prefix,
        mount_point="secret",
        url=vault_credentials["url"],
        token=vault_credentials["token"],
        domain="integration-test",
        project="vault-clear",
    )
    try:
        store.set("A", "1")
        store.set("B", "2")
        store.clear()
        assert len(store.list_keys()) == 0
    finally:
        store.clear()
