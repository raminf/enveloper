"""Integration tests for Alibaba Cloud KMS Secrets Manager store (aliyun).

Disabled by default. To run:
  pip install enveloper[alibaba]
  export ENVELOPER_TEST_ALIBABA=1
  export ENVELOPER_TEST_ALIBABA_REGION=cn-hangzhou   # optional
  export ALIBABA_CLOUD_ACCESS_KEY_ID=...
  export ALIBABA_CLOUD_ACCESS_KEY_SECRET=...
  pytest -m integration_alibaba tests/integration/test_aliyun_sm.py -v
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration_alibaba


def test_aliyun_sm_set_get_delete_list(alibaba_credentials):
    """Set, get, list, and delete a secret in Alibaba Cloud KMS."""
    from enveloper.stores.aliyun_sm import AliyunSmStore

    prefix = "enveloper-integration-test-"
    store = AliyunSmStore(prefix=prefix, region_id=alibaba_credentials)
    key = "ENVELOPER_TEST_KEY"
    value = "secret-value-for-integration-test"

    try:
        store.set(key, value)
        assert store.get(key) == value
        assert key in store.list_keys() or "ENVELOPER_TEST_KEY" in store.list_keys()
    finally:
        store.delete(key)

    assert store.get(key) is None
    assert key not in store.list_keys()


def test_aliyun_sm_clear(alibaba_credentials):
    """Clear all test secrets under the prefix."""
    from enveloper.stores.aliyun_sm import AliyunSmStore

    prefix = "enveloper-integration-test-clear-"
    store = AliyunSmStore(prefix=prefix, region_id=alibaba_credentials)
    try:
        store.set("A", "1")
        store.set("B", "2")
        store.clear()
        assert len(store.list_keys()) == 0
    finally:
        store.clear()
