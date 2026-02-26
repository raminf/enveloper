"""Tests for resolve_store (cloud store prefix/path with domain and project)."""

from __future__ import annotations

import pytest

from enveloper.config import EnveloperConfig
from enveloper.resolve_store import make_cloud_store
from enveloper.stores.aws_ssm import AwsSsmStore
from enveloper.stores.github import GitHubStore
from enveloper.stores.gcp_sm import GcpSmStore
from enveloper.stores.vault import VaultStore


def _minimal_config() -> EnveloperConfig:
    return EnveloperConfig()


def test_aws_default_prefix_includes_domain_and_project(monkeypatch: pytest.MonkeyPatch):
    """When prefix is not provided, store's build_default_prefix is used (plugin API)."""
    captured: dict = {}

    class FakeAwsStore:
        default_namespace = "_default_"

        @classmethod
        def build_default_prefix(cls, domain: str, project: str) -> str:
            return f"/enveloper/{domain}/{project}/"

        def __init__(self, prefix: str, profile: str | None = None, region: str | None = None, **kwargs: object):
            captured["prefix"] = prefix

    monkeypatch.setattr(
        "enveloper.resolve_store.get_store_class",
        lambda name: FakeAwsStore,
    )
    make_cloud_store(
        "aws",
        _minimal_config(),
        "aws",
        None,
        project="myproj",
        prefix=None,
    )
    assert captured["prefix"] == "/enveloper/aws/myproj/"


def test_aws_default_prefix_uses_default_namespace_when_missing(monkeypatch: pytest.MonkeyPatch):
    """When domain or project are empty, store's default_namespace is used (plugin API)."""
    captured: dict = {}

    class FakeAwsStore:
        default_namespace = "_default_"

        @classmethod
        def build_default_prefix(cls, domain: str, project: str) -> str:
            return f"/enveloper/{domain}/{project}/"

        def __init__(self, prefix: str, profile: str | None = None, region: str | None = None, **kwargs: object):
            captured["prefix"] = prefix

    monkeypatch.setattr(
        "enveloper.resolve_store.get_store_class",
        lambda name: FakeAwsStore,
    )
    make_cloud_store(
        "aws",
        _minimal_config(),
        "",
        None,
        project="",
        prefix=None,
    )
    assert captured["prefix"] == "/enveloper/_default_/_default_/"


def test_aws_explicit_prefix_unchanged(monkeypatch: pytest.MonkeyPatch):
    """When user provides --prefix, it is used as-is (no domain/project appended)."""
    captured: dict = {}

    class FakeAwsStore:
        def __init__(self, prefix: str, profile: str | None = None, region: str | None = None, **kwargs: object):
            captured["prefix"] = prefix

    monkeypatch.setattr(
        "enveloper.resolve_store.get_store_class",
        lambda name: FakeAwsStore,
    )
    make_cloud_store(
        "aws",
        _minimal_config(),
        "aws",
        None,
        project="myproj",
        prefix="/myapp/custom/",
    )
    assert captured["prefix"] == "/myapp/custom/"


def test_gcp_default_prefix_uses_double_dash_separator(monkeypatch: pytest.MonkeyPatch):
    """GCP store uses build_default_prefix with -- separator (plugin API)."""
    captured: dict = {}

    class FakeGcpStore:
        default_namespace = "_default_"

        @classmethod
        def build_default_prefix(cls, domain: str, project: str) -> str:
            return f"enveloper--{domain}--{project}--"

        def __init__(self, project_id: str, prefix: str, **kwargs: object):
            captured["prefix"] = prefix

    monkeypatch.setattr(
        "enveloper.resolve_store.get_store_class",
        lambda name: FakeGcpStore,
    )
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "my-gcp-project")
    make_cloud_store(
        "gcp",
        _minimal_config(),
        "prod",
        None,
        project="myapp",
        prefix=None,
    )
    assert captured["prefix"] == "enveloper--prod--myapp--"


def test_vault_default_path_includes_domain_and_project(monkeypatch: pytest.MonkeyPatch):
    """Vault store uses build_default_prefix (plugin API)."""
    captured: dict = {}

    class FakeVaultStore:
        default_namespace = "_default_"

        @classmethod
        def build_default_prefix(cls, domain: str, project: str) -> str:
            return f"enveloper/{domain}/{project}"

        def __init__(self, path: str, mount_point: str = "secret", url: str | None = None, **kwargs: object):
            captured["path"] = path

    monkeypatch.setattr(
        "enveloper.resolve_store.get_store_class",
        lambda name: FakeVaultStore,
    )
    make_cloud_store(
        "vault",
        _minimal_config(),
        "staging",
        None,
        project="svc",
        prefix=None,
    )
    assert captured["path"] == "enveloper/staging/svc"


def test_github_default_prefix_uses_double_underscore(monkeypatch: pytest.MonkeyPatch):
    """GitHub store uses build_default_prefix with __ separator (plugin API)."""
    captured: dict = {}

    class FakeGitHubStore:
        default_namespace = "_default_"

        @classmethod
        def build_default_prefix(cls, domain: str, project: str) -> str:
            return f"ENVELOPER__{domain}__{project}__"

        def __init__(self, prefix: str, repo: str | None = None, **kwargs: object):
            captured["prefix"] = prefix

    monkeypatch.setattr(
        "enveloper.resolve_store.get_store_class",
        lambda name: FakeGitHubStore,
    )
    make_cloud_store(
        "github",
        EnveloperConfig(github_prefix=""),
        "ci",
        None,
        project="api",
        prefix=None,
    )
    assert captured["prefix"] == "ENVELOPER__ci__api__"


def test_real_store_build_default_prefix_api():
    """Real store classes implement the plugin API (default_namespace + build_default_prefix)."""
    assert AwsSsmStore.default_namespace == "_default_"
    assert AwsSsmStore.build_default_prefix("aws", "myproj") == "/enveloper/aws/myproj/"
    assert VaultStore.build_default_prefix("staging", "svc") == "enveloper/staging/svc"
    assert GcpSmStore.build_default_prefix("prod", "myapp") == "enveloper--prod--myapp--"
    assert GitHubStore.build_default_prefix("ci", "api") == "ENVELOPER__ci__api__"
