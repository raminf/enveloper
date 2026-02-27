"""Shared fixtures for cloud store integration tests.

These tests are disabled by default. To run them, set the required env vars
and pass the corresponding marker, e.g.:

  ENVELOPER_TEST_GCP=1 ENVELOPER_TEST_GCP_PROJECT=my-project pytest -m integration_gcp tests/integration/
  ENVELOPER_TEST_AZURE=1 ENVELOPER_TEST_AZURE_VAULT_URL=https://my.vault.azure.net/ pytest -m integration_azure tests/integration/
  ENVELOPER_TEST_AWS=1 pytest -m integration_aws tests/integration/

Unit tests (tests/test_*.py) use autouse mocks for both the keychain and cloud
stores, so they never touch real backends. Integration tests (marked integration_*)
use real backends and are disabled by default.
"""

from __future__ import annotations

import os

import pytest


def _skip_unless(env_flag: str, message: str) -> None:
    if not os.environ.get(env_flag):
        pytest.skip(
            f"{message} Set {env_flag}=1 and provide credentials to run."
        )


@pytest.fixture(scope="module")
def gcp_credentials():
    """Require ENVELOPER_TEST_GCP=1 and ENVELOPER_TEST_GCP_PROJECT."""
    _skip_unless(
        "ENVELOPER_TEST_GCP",
        "GCP integration tests are disabled by default.",
    )
    project = os.environ.get("ENVELOPER_TEST_GCP_PROJECT")
    if not project:
        pytest.skip(
            "Set ENVELOPER_TEST_GCP_PROJECT to your GCP project ID for GCP integration tests."
        )
    return project


@pytest.fixture(scope="module")
def azure_credentials():
    """Require ENVELOPER_TEST_AZURE=1 and ENVELOPER_TEST_AZURE_VAULT_URL."""
    _skip_unless(
        "ENVELOPER_TEST_AZURE",
        "Azure integration tests are disabled by default.",
    )
    vault_url = os.environ.get("ENVELOPER_TEST_AZURE_VAULT_URL")
    if not vault_url:
        pytest.skip(
            "Set ENVELOPER_TEST_AZURE_VAULT_URL to your Key Vault URL for Azure integration tests."
        )
    return vault_url


@pytest.fixture(scope="module")
def aws_credentials():
    """Require ENVELOPER_TEST_AWS=1 (AWS credentials via env or profile)."""
    _skip_unless(
        "ENVELOPER_TEST_AWS",
        "AWS integration tests are disabled by default.",
    )


@pytest.fixture(scope="module")
def alibaba_credentials():
    """Require ENVELOPER_TEST_ALIBABA=1 and Alibaba credentials (env or config)."""
    _skip_unless(
        "ENVELOPER_TEST_ALIBABA",
        "Alibaba Cloud integration tests are disabled by default.",
    )
    if not os.environ.get("ALIBABA_CLOUD_ACCESS_KEY_ID") or not os.environ.get("ALIBABA_CLOUD_ACCESS_KEY_SECRET"):
        pytest.skip(
            "Set ALIBABA_CLOUD_ACCESS_KEY_ID and ALIBABA_CLOUD_ACCESS_KEY_SECRET for Alibaba integration tests."
        )
    return os.environ.get("ENVELOPER_TEST_ALIBABA_REGION", "cn-hangzhou")
