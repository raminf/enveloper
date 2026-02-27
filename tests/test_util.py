"""Tests for enveloper.util."""

from __future__ import annotations

from enveloper.util import key_to_export_name, strip_domain_prefix


def test_strip_domain_prefix_no_slash():
    """Key without slash is unchanged."""
    assert strip_domain_prefix("API_KEY") == "API_KEY"
    assert strip_domain_prefix("DATABASE_URL") == "DATABASE_URL"


def test_strip_domain_prefix_one_segment():
    """Key with one slash: return part after slash."""
    assert strip_domain_prefix("prod/API_KEY") == "API_KEY"
    assert strip_domain_prefix("default/SECRET") == "SECRET"


def test_strip_domain_prefix_multiple_segments():
    """Key with multiple slashes: return part after last slash."""
    assert strip_domain_prefix("myproject/prod/API_KEY") == "API_KEY"
    assert strip_domain_prefix("a/b/c") == "c"


def test_strip_domain_prefix_empty_after_slash():
    """Edge case: key ends with slash."""
    assert strip_domain_prefix("prod/") == ""


def test_key_to_export_name_parsed():
    """key_to_export_name returns name when store parses key (prefix/version stripped)."""
    from enveloper.stores.aws_ssm import AwsSsmStore

    store = AwsSsmStore(
        prefix=f"{AwsSsmStore.key_separator}{AwsSsmStore.prefix}/dom/proj/",
        domain="dom",
        project="proj",
    )
    full_key = store.key_separator + store.build_key(
        name="API_KEY", project="proj", domain="dom", version="1.0.0"
    )
    assert store.parse_key(full_key) is not None
    assert key_to_export_name(store, full_key) == "API_KEY"


def test_key_to_export_name_fallback():
    """key_to_export_name returns last segment when parse fails."""
    from enveloper.stores.file_store import FileStore

    store = FileStore(path=".env")
    assert key_to_export_name(store, "plain_key") == "plain_key"
    sep = store.key_separator
    assert key_to_export_name(store, f"a{sep}b{sep}c") == "c"
