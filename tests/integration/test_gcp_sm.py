"""Integration tests for GCP Secret Manager store (gcp).

Disabled by default. To run:
  pip install enveloper[gcp]
  export ENVELOPER_TEST_GCP=1
  export ENVELOPER_TEST_GCP_PROJECT=your-gcp-project-id
  # Use Application Default Credentials (gcloud auth application-default login)
  # or GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
  pytest -m integration_gcp tests/integration/test_gcp_sm.py -v
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration_gcp


def test_gcp_sm_set_get_delete_list(gcp_credentials):
    """Set, get, list, and delete a secret in GCP Secret Manager."""
    from enveloper.stores.gcp_sm import GcpSmStore

    prefix = "enveloper-integration-test-"
    store = GcpSmStore(project_id=gcp_credentials, prefix=prefix)
    key = "ENVELOPER_TEST_KEY"
    value = "secret-value-for-integration-test"

    try:
        store.set(key, value)
        assert store.get(key) == value
        assert key in store.list_keys()
    finally:
        store.delete(key)

    assert store.get(key) is None
    assert key not in store.list_keys()


def test_gcp_sm_clear(gcp_credentials):
    """Clear all secrets under the test prefix."""
    from enveloper.stores.gcp_sm import GcpSmStore

    prefix = "enveloper-integration-test-clear-"
    store = GcpSmStore(project_id=gcp_credentials, prefix=prefix)
    try:
        store.set("A", "1")
        store.set("B", "2")
        assert len(store.list_keys()) >= 2
        store.clear()
        assert store.list_keys() == []
    finally:
        store.clear()
