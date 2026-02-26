"""Integration tests for Azure Key Vault store (azure).

Disabled by default. To run:
  pip install enveloper[azure]
  export ENVELOPER_TEST_AZURE=1
  export ENVELOPER_TEST_AZURE_VAULT_URL=https://your-vault.vault.azure.net/
  # Use DefaultAzureCredential (Azure CLI login, env vars, or managed identity)
  pytest -m integration_azure tests/integration/test_azure_kv.py -v
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration_azure


def test_azure_kv_set_get_delete_list(azure_credentials):
    """Set, get, list, and delete a secret in Azure Key Vault."""
    from enveloper.stores.azure_kv import AzureKvStore

    prefix = "enveloper-integration-test-"
    store = AzureKvStore(vault_url=azure_credentials, prefix=prefix)
    key = "ENVELOPER_TEST_KEY"
    value = "secret-value-for-integration-test"

    try:
        store.set(key, value)
        assert store.get(key) == value
        # Azure returns sanitized key names (lowercase, hyphens)
        assert any("enveloper-test-key" in k.lower() for k in store.list_keys())
    finally:
        store.delete(key)

    assert store.get(key) is None


def test_azure_kv_clear(azure_credentials):
    """Clear all test secrets under the prefix."""
    from enveloper.stores.azure_kv import AzureKvStore

    prefix = "enveloper-integration-test-clear-"
    store = AzureKvStore(vault_url=azure_credentials, prefix=prefix)
    try:
        store.set("A", "1")
        store.set("B", "2")
        store.clear()
        assert len(store.list_keys()) == 0
    finally:
        store.clear()
