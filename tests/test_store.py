"""Tests for SecretStore base class: sanitization, build_key, parse_key."""

from __future__ import annotations

import pytest

from enveloper.security import SanitizationError
from enveloper.stores.aws_ssm import AwsSsmStore


def test_sanitize_key_segment_rejects_separator_and_punctuation():
    """Key segments reject separators and punctuation-heavy values."""
    with pytest.raises(SanitizationError):
        AwsSsmStore.sanitize_key_segment("a/b")
    with pytest.raises(SanitizationError):
        AwsSsmStore.sanitize_key_segment("prod staging")
    with pytest.raises(SanitizationError):
        AwsSsmStore.sanitize_secret_key("KEY-WITH-DASH")


def test_sanitize_key_segment_empty_or_whitespace_returns_default():
    """Empty or whitespace segment becomes default_namespace."""
    out = AwsSsmStore.sanitize_key_segment("")
    assert out == AwsSsmStore.default_namespace
    out = AwsSsmStore.sanitize_key_segment("   ")
    assert out == AwsSsmStore.default_namespace


def test_build_key_with_separator_in_domain_is_rejected():
    """build_key rejects domains containing the path separator."""
    store = AwsSsmStore(prefix="/envr/", domain="dom", project="proj")
    with pytest.raises(SanitizationError):
        store.build_key(name="API_KEY", domain="a/b", project="proj", version="1.0.0")


def test_build_key_with_separator_in_project_is_rejected():
    """build_key rejects projects containing the path separator."""
    store = AwsSsmStore(prefix="/envr/", domain="dom", project="proj")
    with pytest.raises(SanitizationError):
        store.build_key(name="K", domain="dom", project="x/y", version="1.0.0")


def test_build_key_parse_key_roundtrip_with_valid_segments():
    """build_key then parse_key round-trips for valid ASCII segments."""
    store = AwsSsmStore(prefix="/envr/", domain="d", project="p")
    key = store.build_key(name="FOO", domain="prod", project="p", version="1.0.0")
    parsed = store.parse_key(key)
    assert parsed["domain"] == "prod"
    assert parsed["name"] == "FOO"
    with pytest.raises(SanitizationError):
        store.build_key(name="BAR", domain="prod🔥", project="p", version="1.0.0")


def test_aws_store_invalid_version_raises():
    """AwsSsmStore with invalid semver version raises ValueError (no bad key written)."""
    with pytest.raises(ValueError, match="Invalid version|semver"):
        AwsSsmStore(version="1.0", domain="d", project="p")
    with pytest.raises(ValueError, match="Invalid version|semver"):
        AwsSsmStore(version="v1.0.0", domain="d", project="p")
    with pytest.raises(ValueError, match="Invalid version|semver"):
        AwsSsmStore(version="", domain="d", project="p")
