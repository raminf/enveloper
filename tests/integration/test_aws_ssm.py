"""Integration tests for AWS SSM Parameter Store (aws).

Disabled by default. To run:
  pip install enveloper[aws]
  export ENVELOPER_TEST_AWS=1
  export ENVELOPER_TEST_AWS_PREFIX=/enveloper-integration-test/
  # Use AWS credentials (env vars, profile, or IAM role)
  pytest -m integration_aws tests/integration/test_aws_ssm.py -v
"""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.integration_aws


@pytest.fixture(scope="module")
def aws_prefix():
    """Prefix for SSM parameters (avoids clashing with real data)."""
    return os.environ.get("ENVELOPER_TEST_AWS_PREFIX", "/enveloper-integration-test/")


def test_aws_ssm_set_get_delete_list(aws_credentials, aws_prefix):
    """Set, get, list, and delete a parameter in AWS SSM."""
    from enveloper.stores.aws_ssm import AwsSsmStore

    store = AwsSsmStore(prefix=aws_prefix)
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


def test_aws_ssm_clear(aws_credentials, aws_prefix):
    """Clear all parameters under the test prefix."""
    from enveloper.stores.aws_ssm import AwsSsmStore

    store = AwsSsmStore(prefix=aws_prefix)
    try:
        store.set("A", "1")
        store.set("B", "2")
        assert len(store.list_keys()) >= 2
        store.clear()
        assert store.list_keys() == []
    finally:
        store.clear()
