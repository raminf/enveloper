"""Tests for enveloper.util."""

from __future__ import annotations

from enveloper.util import strip_domain_prefix


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
