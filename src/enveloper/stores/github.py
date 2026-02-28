# Copyright (c) 2026 Ramin Firoozye
# SPDX-License-Identifier: AGPL-3.0-or-later

"""GitHubStore -- push secrets to GitHub Actions Secrets via the ``gh`` CLI.

This is a **push-only** store: GitHub Secrets are write-only by design
(you can list names but never read values back).

Requires the ``gh`` CLI to be installed and authenticated.
"""

from __future__ import annotations

import json
import shutil
import subprocess

from enveloper.store import DEFAULT_NAMESPACE, DEFAULT_VERSION, SecretStore, is_valid_semver

_MISSING_GH = (
    "The 'gh' CLI is required for the github store. "
    "Install it from https://cli.github.com/ and run 'gh auth login'."
)


class GitHubStore(SecretStore):
    """Push secrets to GitHub Actions repository secrets.

    Values are sent directly via ``gh secret set`` with no intermediate files.
    Key format: ENVR__{domain}__{project}__{version}__{name} (version uses _ for dots).
    """

    service_name: str = "github"
    service_display_name: str = "GitHub Actions encrypted secrets"
    service_doc_url: str = "https://docs.github.com/en/actions/security-guides/encrypted-secrets"

    default_namespace: str = "_default_"
    prefix: str = "ENVR"  # GitHub env var style, uppercase
    # GitHub doesn't support dots in key names, so use underscore
    version_separator: str = "_"
    key_separator: str = "__"

    @classmethod
    def build_default_prefix(cls, domain: str, project: str) -> str:
        """Default prefix: ENVR__{domain}__{project}__ (separator __)."""
        d = cls.sanitize_key_segment(domain)
        p = cls.sanitize_key_segment(project)
        return f"{cls.prefix}__{d}__{p}__"

    def __init__(
        self,
        prefix: str = "",
        repo: str | None = None,
        version: str = DEFAULT_VERSION,
        domain: str = DEFAULT_NAMESPACE,
        project: str = DEFAULT_NAMESPACE,
        **kwargs: object,
    ) -> None:
        self._prefix = prefix
        self._repo = repo
        self._version = version
        self._domain = domain
        self._project = project
        # Validate version format
        if not is_valid_semver(version):
            raise ValueError(f"Invalid version format: {version}. Must be valid semver (e.g., 1.0.0)")
        if shutil.which("gh") is None:
            raise RuntimeError(_MISSING_GH)

    def _gh(self, *args: str, input_data: str | None = None) -> subprocess.CompletedProcess[str]:
        cmd = ["gh", "secret", *args]
        if self._repo:
            cmd.extend(["--repo", self._repo])
        return subprocess.run(
            cmd,
            input=input_data,
            capture_output=True,
            text=True,
            check=True,
        )

    def _resolve_key(self, key: str) -> str:
        """Return full composite key; if key is short name, build full key with domain/project/version."""
        if self.parse_key(key) is not None:
            return key
        return self.build_key(
            name=key, project=self._project, domain=self._domain, version=self._version
        )

    def _prefixed(self, key: str) -> str:
        """Return the secret name for GitHub. Use key as-is so workflows can use secrets.KEYNAME."""
        return key

    def get(self, key: str) -> str | None:
        raise NotImplementedError(
            "GitHub Secrets are write-only. Values cannot be read back."
        )

    def set(self, key: str, value: str) -> None:
        self._gh("set", self._prefixed(key), "--body", value)

    def delete(self, key: str) -> None:
        try:
            self._gh("delete", self._prefixed(key))
        except subprocess.CalledProcessError:
            pass

    def list_keys(self) -> list[str]:
        """List secret names (simple key names) so workflows use secrets.KEYNAME. Values never exposed."""
        try:
            result = self._gh("list", "--json", "name")
            secrets = json.loads(result.stdout)
            return sorted(s["name"] for s in secrets)
        except (subprocess.CalledProcessError, json.JSONDecodeError):
            return []

