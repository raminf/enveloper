"""GitHubStore -- push secrets to GitHub Actions Secrets via the ``gh`` CLI.

This is a **push-only** store: GitHub Secrets are write-only by design
(you can list names but never read values back).

Requires the ``gh`` CLI to be installed and authenticated.
"""

from __future__ import annotations

import json
import shutil
import subprocess

import re

from enveloper.store import DEFAULT_NAMESPACE, SecretStore

_MISSING_GH = (
    "The 'gh' CLI is required for the github store. "
    "Install it from https://cli.github.com/ and run 'gh auth login'."
)


def _sanitize_github_segment(s: str) -> str:
    """GitHub secret names: letters, numbers, underscores, hyphens."""
    if not s or not s.strip():
        return DEFAULT_NAMESPACE
    return re.sub(r"[^a-zA-Z0-9_-]", "_", s).strip() or DEFAULT_NAMESPACE


class GitHubStore(SecretStore):
    """Push secrets to GitHub Actions repository secrets.

    Values are sent directly via ``gh secret set`` with no intermediate files.
    """

    default_namespace: str = "_default_"

    @classmethod
    def build_default_prefix(cls, domain: str, project: str) -> str:
        """Default prefix: ENVELOPER__{domain}__{project}__ (separator __)."""
        d = _sanitize_github_segment(domain)
        p = _sanitize_github_segment(project)
        return f"ENVELOPER__{d}__{p}__"

    def __init__(self, prefix: str = "", repo: str | None = None) -> None:
        self._prefix = prefix
        self._repo = repo
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

    def _prefixed(self, key: str) -> str:
        return f"{self._prefix}{key}"

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
        """List secret names (values are never exposed)."""
        try:
            result = self._gh("list", "--json", "name")
            secrets = json.loads(result.stdout)
            names = [s["name"] for s in secrets]
            if self._prefix:
                names = [
                    n[len(self._prefix) :]
                    for n in names
                    if n.startswith(self._prefix)
                ]
            return sorted(names)
        except (subprocess.CalledProcessError, json.JSONDecodeError):
            return []

    def clear(self) -> None:
        for key in self.list_keys():
            self.delete(key)
