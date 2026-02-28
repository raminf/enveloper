"""Tests for resolve_store (cloud store prefix/path with domain and project)."""

from __future__ import annotations

import os
from typing import cast

import pytest

from enveloper.config import EnveloperConfig
from enveloper.resolve_store import make_cloud_store
from enveloper.store import DEFAULT_PREFIX
from enveloper.stores.aws_ssm import AwsSsmStore
from enveloper.stores.gcp_sm import GcpSmStore
from enveloper.stores.github import GitHubStore
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
            return f"/{DEFAULT_PREFIX}/{domain}/{project}/"

        def __init__(self, prefix: str, profile: str | None = None, region: str | None = None, **kwargs: object):
            captured["prefix"] = prefix

        @classmethod
        def from_config(
            cls,
            domain: str,
            project: str,
            config: object,
            prefix: str | None = None,
            env_name: str | None = None,
            **kwargs: object,
        ) -> "FakeAwsStore":
            """Create store from config using build_default_prefix if no prefix provided."""
            if prefix is None:
                prefix = cls.build_default_prefix(domain, project)
            return cls(
                prefix=prefix,
                profile=cast(str | None, kwargs.get("profile")),
                region=cast(str | None, kwargs.get("region")),
            )

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
    assert captured["prefix"] == f"/{DEFAULT_PREFIX}/aws/myproj/"


def test_aws_default_prefix_uses_default_namespace_when_missing(monkeypatch: pytest.MonkeyPatch):
    """When domain or project are empty, store's default_namespace is used (plugin API)."""
    captured: dict = {}

    class FakeAwsStore:
        default_namespace = "_default_"

        @classmethod
        def build_default_prefix(cls, domain: str, project: str) -> str:
            return f"/{DEFAULT_PREFIX}/{domain}/{project}/"

        def __init__(self, prefix: str, profile: str | None = None, region: str | None = None, **kwargs: object):
            captured["prefix"] = prefix

        @classmethod
        def from_config(
            cls,
            domain: str,
            project: str,
            config: object,
            prefix: str | None = None,
            env_name: str | None = None,
            **kwargs: object,
        ) -> "FakeAwsStore":
            """Create store from config using build_default_prefix if no prefix provided."""
            if prefix is None:
                prefix = cls.build_default_prefix(domain, project)
            return cls(
                prefix=prefix,
                profile=cast(str | None, kwargs.get("profile")),
                region=cast(str | None, kwargs.get("region")),
            )

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
    assert captured["prefix"] == f"/{DEFAULT_PREFIX}/_default_/_default_/"


def test_aws_explicit_prefix_unchanged(monkeypatch: pytest.MonkeyPatch):
    """When user provides --prefix, it is used as-is (no domain/project appended)."""
    captured: dict = {}

    class FakeAwsStore:
        @classmethod
        def build_default_prefix(cls, domain: str, project: str) -> str:
            return f"/{DEFAULT_PREFIX}/{domain}/{project}/"

        def __init__(self, prefix: str, profile: str | None = None, region: str | None = None, **kwargs: object):
            captured["prefix"] = prefix

        @classmethod
        def from_config(
            cls,
            domain: str,
            project: str,
            config: object,
            prefix: str | None = None,
            env_name: str | None = None,
            **kwargs: object,
        ) -> "FakeAwsStore":
            """Create store from config using provided prefix."""
            # Don't pass prefix again since it's already a positional arg
            prefix_str = prefix or cls.build_default_prefix(domain, project)
            return cls(
                prefix=prefix_str,
                profile=cast(str | None, kwargs.get("profile")),
                region=cast(str | None, kwargs.get("region")),
            )

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
            return f"{DEFAULT_PREFIX}--{domain}--{project}--"

        def __init__(self, project_id: str, prefix: str, **kwargs: object):
            captured["prefix"] = prefix

        @classmethod
        def from_config(
            cls,
            domain: str,
            project: str,
            config: object,
            prefix: str | None = None,
            env_name: str | None = None,
            **kwargs: object,
        ) -> "FakeGcpStore":
            """Create store from config using build_default_prefix if no prefix provided."""
            if prefix is None:
                prefix = cls.build_default_prefix(domain, project)
            # Get project_id from config or env
            project_id = (
                kwargs.get("project_id")
                or getattr(config, "gcp_project", "")
                or os.environ.get("GOOGLE_CLOUD_PROJECT", "enveloper")
            )
            return cls(project_id=cast(str, project_id), prefix=prefix)

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
    assert captured["prefix"] == f"{DEFAULT_PREFIX}--prod--myapp--"


def test_vault_default_path_includes_domain_and_project(monkeypatch: pytest.MonkeyPatch):
    """Vault store uses build_default_prefix (plugin API)."""
    captured: dict = {}

    class FakeVaultStore:
        default_namespace = "_default_"

        @classmethod
        def build_default_prefix(cls, domain: str, project: str) -> str:
            return f"{DEFAULT_PREFIX}/{domain}/{project}"

        def __init__(self, path: str, mount_point: str = "secret", url: str | None = None, **kwargs: object):
            captured["path"] = path

        @classmethod
        def from_config(
            cls,
            domain: str,
            project: str,
            config: object,
            prefix: str | None = None,
            env_name: str | None = None,
            **kwargs: object,
        ) -> "FakeVaultStore":
            """Create store from config using build_default_prefix if no prefix provided."""
            if prefix is None:
                prefix = cls.build_default_prefix(domain, project)
            # Use path instead of prefix for vault
            return cls(
                path=prefix,
                mount_point=cast(str, kwargs.get("mount_point", "secret")),
                url=cast(str | None, kwargs.get("url")),
            )

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
    assert captured["path"] == f"{DEFAULT_PREFIX}/staging/svc"


def test_github_default_prefix_uses_double_underscore(monkeypatch: pytest.MonkeyPatch):
    """GitHub store uses build_default_prefix with __ separator (plugin API)."""
    captured: dict = {}

    class FakeGitHubStore:
        default_namespace = "_default_"

        @classmethod
        def build_default_prefix(cls, domain: str, project: str) -> str:
            return f"ENVR__{domain}__{project}__"

        def __init__(self, prefix: str, repo: str | None = None, **kwargs: object):
            captured["prefix"] = prefix

        @classmethod
        def from_config(
            cls,
            domain: str,
            project: str,
            config: object,
            prefix: str | None = None,
            env_name: str | None = None,
            **kwargs: object,
        ) -> "FakeGitHubStore":
            """Create store from config using build_default_prefix if no prefix provided."""
            if prefix is None:
                prefix = cls.build_default_prefix(domain, project)
            return cls(prefix=prefix, repo=cast(str | None, kwargs.get("repo")))

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
    assert captured["prefix"] == "ENVR__ci__api__"


def test_real_store_build_default_prefix_api():
    """Real store classes implement the plugin API (default_namespace + build_default_prefix)."""
    assert AwsSsmStore.default_namespace == "_default_"
    sep = AwsSsmStore.key_separator
    pre = AwsSsmStore.prefix
    assert AwsSsmStore.build_default_prefix("aws", "myproj") == f"{sep}{pre}{sep}aws{sep}myproj{sep}"
    assert VaultStore.build_default_prefix("staging", "svc") == f"{DEFAULT_PREFIX}/staging/svc"
    assert GcpSmStore.build_default_prefix("prod", "myapp") == f"{DEFAULT_PREFIX}--prod--myapp--"
    assert GitHubStore.build_default_prefix("ci", "api") == "ENVR__ci__api__"
