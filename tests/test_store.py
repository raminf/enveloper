"""Tests for SecretStore base class: sanitization, build_key, parse_key."""

from __future__ import annotations

import pytest

from enveloper.store import DEFAULT_VERSION, SecretStore
from enveloper.stores.aws_ssm import AwsSsmStore


def test_sanitize_key_segment_replaces_separator():
    """Key segment containing key_separator is replaced so key path is not broken."""
    sep = AwsSsmStore.key_separator  # "/"
    assert sep == "/"
    # Domain with slash becomes underscore
    out = AwsSsmStore.sanitize_key_segment("a/b")
    assert out == "a_b"
    out = AwsSsmStore.sanitize_key_segment("prod/staging")
    assert out == "prod_staging"
    # Project with slash
    out = AwsSsmStore.sanitize_key_segment("x/y")
    assert out == "x_y"
    # Name with slash
    out = AwsSsmStore.sanitize_key_segment("KEY/WITH/SLASH")
    assert out == "KEY_WITH_SLASH"


def test_sanitize_key_segment_empty_or_whitespace_returns_default():
    """Empty or whitespace segment becomes default_namespace."""
    out = AwsSsmStore.sanitize_key_segment("")
    assert out == AwsSsmStore.default_namespace
    out = AwsSsmStore.sanitize_key_segment("   ")
    assert out == AwsSsmStore.default_namespace


def test_build_key_with_separator_in_domain_produces_safe_key():
    """build_key with domain containing key_separator produces a key that parse_key can parse."""
    store = AwsSsmStore(prefix="/envr/", domain="dom", project="proj")
    key = store.build_key(name="API_KEY", project="proj", domain="a/b", version="1.0.0")
    assert "a_b" in key
    assert "a/b" not in key or key.count("/") == 4  # path segments, not domain-internal
    parsed = store.parse_key(key)
    assert parsed is not None
    assert parsed["domain"] == "a_b"
    assert parsed["name"] == "API_KEY"


def test_build_key_with_separator_in_project_produces_safe_key():
    """build_key with project containing key_separator produces a key that parse_key can parse."""
    store = AwsSsmStore(prefix="/envr/", domain="dom", project="proj")
    key = store.build_key(name="K", project="x/y", domain="dom", version="1.0.0")
    assert "x_y" in key
    parsed = store.parse_key(key)
    assert parsed is not None
    assert parsed["project"] == "x_y"


def test_build_key_parse_key_roundtrip_with_sanitized_segments():
    """build_key then parse_key round-trips when segments contain separator or emoji."""
    store = AwsSsmStore(prefix="/envr/", domain="d", project="p")
    # Segment with separator
    key = store.build_key(name="FOO", project="p", domain="a/b", version="1.0.0")
    parsed = store.parse_key(key)
    assert parsed["domain"] == "a_b"
    assert parsed["name"] == "FOO"
    # Segment with emoji (should be preserved or sanitized; must not break parse)
    key2 = store.build_key(name="BAR", project="p", domain="prod🔥", version="1.0.0")
    parsed2 = store.parse_key(key2)
    assert parsed2 is not None
    assert parsed2["name"] == "BAR"


def test_aws_store_invalid_version_raises():
    """AwsSsmStore with invalid semver version raises ValueError (no bad key written)."""
    with pytest.raises(ValueError, match="Invalid version|semver"):
        AwsSsmStore(version="1.0", domain="d", project="p")
    with pytest.raises(ValueError, match="Invalid version|semver"):
        AwsSsmStore(version="v1.0.0", domain="d", project="p")
    with pytest.raises(ValueError, match="Invalid version|semver"):
        AwsSsmStore(version="", domain="d", project="p")
