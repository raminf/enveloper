# Copyright (c) 2026 Ramin Firoozye
# SPDX-License-Identifier: AGPL-3.0-or-later

""".enveloper.toml configuration loading.

If ``~/.enveloper`` exists, loads ``~/.enveloper/.enveloper.toml``.
Otherwise searches upward from cwd for ``.enveloper.toml``.
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class DomainConfig:
    """Per-domain settings from config file."""

    env_file: str | None = None
    ssm_prefix: str | None = None


@dataclass
class EnveloperConfig:
    """Resolved configuration for the current invocation."""

    project: str = "_default_"
    service: str | None = None
    domains: dict[str, DomainConfig] = field(default_factory=dict)
    aws_profile: str = "default"
    aws_region: str | None = None
    github_prefix: str = ""
    vault_url: str | None = None
    vault_mount: str = "secret"
    gcp_project: str | None = None
    azure_vault_url: str | None = None
    aliyun_region_id: str = "cn-hangzhou"
    aliyun_access_key_id: str | None = None
    aliyun_access_key_secret: str | None = None
    config_path: Path | None = None

    def resolve_ssm_prefix(self, domain: str, env: str | None = None) -> str | None:
        """Expand ``{env}`` placeholder in the domain's ssm_prefix."""
        dc = self.domains.get(domain)
        if dc is None or dc.ssm_prefix is None:
            return None
        prefix = dc.ssm_prefix
        if "{env}" in prefix:
            resolved_env = env or os.environ.get("STILLUP_ENV_NAME", "test")
            prefix = prefix.replace("{env}", resolved_env)
        return prefix


def _user_enveloper_dir() -> Path:
    """Return ~/.enveloper (expanded)."""
    return Path.home() / ".enveloper"


def find_config_file(start: Path | None = None) -> Path | None:
    """Find config file: ~/.enveloper/.enveloper.toml if ~/.enveloper exists, else walk upward from cwd."""
    user_dir = _user_enveloper_dir()
    if user_dir.is_dir():
        candidate = user_dir / ".enveloper.toml"
        if candidate.is_file():
            return candidate
    cur = (start or Path.cwd()).resolve()
    while True:
        candidate = cur / ".enveloper.toml"
        if candidate.is_file():
            return candidate
        if cur.parent == cur:
            return None
        cur = cur.parent


def load_config(path: Path | None = None) -> EnveloperConfig:
    """Load and return config.  Returns defaults if no file found."""
    if path is None:
        path = find_config_file()
    if path is None:
        return EnveloperConfig()

    raw: dict[str, Any] = tomllib.loads(path.read_text())
    section = raw.get("enveloper", {})

    domains: dict[str, DomainConfig] = {}
    for name, dcfg in section.get("domains", {}).items():
        domains[name] = DomainConfig(
            env_file=dcfg.get("env_file"),
            ssm_prefix=dcfg.get("ssm_prefix"),
        )

    aws = section.get("aws", {})
    gh = section.get("github", {})
    vault = section.get("vault", {})
    gcp = section.get("gcp", {})
    azure = section.get("azure", {})
    aliyun = section.get("aliyun", {})

    return EnveloperConfig(
        project=section.get("project", "_default_"),
        service=section.get("service"),
        domains=domains,
        aws_profile=aws.get("profile", "default"),
        aws_region=aws.get("region"),
        github_prefix=gh.get("prefix", ""),
        vault_url=vault.get("url"),
        vault_mount=vault.get("mount", "secret"),
        gcp_project=gcp.get("project"),
        azure_vault_url=azure.get("vault_url"),
        aliyun_region_id=aliyun.get("region_id", "cn-hangzhou"),
        aliyun_access_key_id=aliyun.get("access_key_id"),
        aliyun_access_key_secret=aliyun.get("access_key_secret"),
        config_path=path,
    )
