# Copyright (c) 2026 Ramin Firoozye
# SPDX-License-Identifier: AGPL-3.0-or-later

"""KeychainStore -- local secret storage via the ``keyring`` library.

Cross-platform: macOS Keychain, Linux SecretService (GNOME Keyring / KDE
Wallet), Windows Credential Locker.

Secrets are stored under service ``envr:{project}`` (prefix from base store)
with username ``{domain}/{version}/{key}``.  A manifest entry at ``{domain}/__keys__``
holds a JSON list of key names so we can enumerate without scanning the whole
keychain.
"""

from __future__ import annotations

import json

import keyring

from enveloper.store import DEFAULT_PREFIX, DEFAULT_VERSION, SecretStore, is_valid_semver

_MANIFEST_KEY = "__keys__"
_GLOBAL_REGISTRY_SERVICE = "envr:__registry__"


_KEYRING_DOC = "https://github.com/jaraco/keyring"
_SERVICE_PLATFORMS: list[tuple[str, str, str]] = [
    ("local (MacOS)", "macOS Keychain", "https://support.apple.com/guide/keychain-access/welcome/mac"),
    ("local (Windows)", "Windows Credential Locker", "https://learn.microsoft.com/en-us/windows/win32/secauthn/credential-manager"),
    ("local (Linux)", "Linux Secret Service", "https://specifications.freedesktop.org/secret-service/"),
]


class KeychainStore(SecretStore):
    """Read/write secrets in the OS keychain, scoped by project and domain."""

    service_name: str = "local"
    service_display_name: str = "System keychain"
    service_doc_url: str = _KEYRING_DOC

    # Keychain can use dots; use underscore for compatibility with keyring usernames
    version_separator: str = "_"
    key_separator: str = "/"
    prefix: str = DEFAULT_PREFIX

    @classmethod
    def get_service_rows(cls) -> list[tuple[str, str, str]]:
        return list(_SERVICE_PLATFORMS)

    def __init__(
        self,
        project: str = "_default_",
        domain: str | None = None,
        version: str = DEFAULT_VERSION,
    ) -> None:
        self._service = f"{self.prefix}:{project}"
        self._domain = domain
        self._version = version
        # Validate version format
        if not is_valid_semver(version):
            raise ValueError(f"Invalid version format: {version}. Must be valid semver (e.g., 1.0.0)")

    def _username(self, key: str) -> str:
        if self._domain:
            return f"{self._domain}/{self._version}/{key}"
        return f"{self._version}/{key}"

    def _manifest_username(self, domain: str | None = None) -> str:
        d = domain or self._domain or "_global"
        return f"{d}/{_MANIFEST_KEY}"

    def _read_manifest(self, domain: str | None = None) -> list[str]:
        raw = keyring.get_password(self._service, self._manifest_username(domain))
        if raw is None:
            return []
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return []

    def _write_manifest(self, keys: list[str], domain: str | None = None) -> None:
        keyring.set_password(
            self._service, self._manifest_username(domain), json.dumps(sorted(set(keys)))
        )

    def get(self, key: str) -> str | None:
        return keyring.get_password(self._service, self._username(key))

    def set(self, key: str, value: str) -> None:
        keyring.set_password(self._service, self._username(key), value)
        manifest = self._read_manifest()
        if key not in manifest:
            manifest.append(key)
            self._write_manifest(manifest)

    def delete(self, key: str) -> None:
        try:
            keyring.delete_password(self._service, self._username(key))
        except keyring.errors.PasswordDeleteError:
            pass
        manifest = self._read_manifest()
        if key in manifest:
            manifest.remove(key)
            self._write_manifest(manifest)
            # If domain is now empty, remove it from the domain list so list_domains() doesn't show it
            if not manifest and self._domain:
                self.unregister_domain(self._domain)

    def list_keys(self) -> list[str]:
        return self._read_manifest()

    def clear(self) -> None:
        for key in self._read_manifest():
            try:
                keyring.delete_password(self._service, self._username(key))
            except keyring.errors.PasswordDeleteError:
                pass
        try:
            keyring.delete_password(self._service, self._manifest_username())
        except keyring.errors.PasswordDeleteError:
            pass
        if self._domain:
            self.unregister_domain(self._domain)

    def list_domains(self) -> list[str]:
        """Return domain names that have a manifest entry.

        This is a best-effort scan: it checks known domain names stored in a
        top-level ``__domains__`` manifest.
        """
        raw = keyring.get_password(self._service, "__domains__")
        if raw is None:
            return []
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return []

    def register_domain(self, domain: str) -> None:
        """Add *domain* to the top-level domain manifest."""
        domains = self.list_domains()
        if domain not in domains:
            domains.append(domain)
            keyring.set_password(self._service, "__domains__", json.dumps(sorted(domains)))

    def unregister_domain(self, domain: str) -> None:
        """Remove *domain* from the top-level domain manifest (e.g. when last key in domain is deleted)."""
        domains = self.list_domains()
        if domain not in domains:
            return
        domains = [d for d in domains if d != domain]
        if domains:
            keyring.set_password(self._service, "__domains__", json.dumps(sorted(domains)))
        else:
            try:
                keyring.delete_password(self._service, "__domains__")
            except keyring.errors.PasswordDeleteError:
                pass

    # ------------------------------------------------------------------
    # Global project registry (shared across all KeychainStore instances)
    # ------------------------------------------------------------------

    @classmethod
    def list_all_projects(cls) -> list[str]:
        """Return all project names ever registered (global registry)."""
        raw = keyring.get_password(_GLOBAL_REGISTRY_SERVICE, "__projects__")
        if raw is None:
            return []
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return []

    @classmethod
    def register_global_project(cls, project: str) -> None:
        """Add *project* to the global project registry."""
        projects = cls.list_all_projects()
        if project not in projects:
            projects.append(project)
            keyring.set_password(
                _GLOBAL_REGISTRY_SERVICE, "__projects__", json.dumps(sorted(projects))
            )

    @classmethod
    def unregister_global_project(cls, project: str) -> None:
        """Remove *project* from the global project registry."""
        projects = cls.list_all_projects()
        if project not in projects:
            return
        projects = [p for p in projects if p != project]
        if projects:
            keyring.set_password(
                _GLOBAL_REGISTRY_SERVICE, "__projects__", json.dumps(sorted(projects))
            )
        else:
            try:
                keyring.delete_password(_GLOBAL_REGISTRY_SERVICE, "__projects__")
            except keyring.errors.PasswordDeleteError:
                pass

    @classmethod
    def list_all_domains(cls) -> dict[str, list[str]]:
        """Return a mapping of project -> domains for all registered projects."""
        result: dict[str, list[str]] = {}
        for project in cls.list_all_projects():
            store = cls(project=project)
            domains = store.list_domains()
            if domains:
                result[project] = domains
        return result

    @classmethod
    def list_projects_for_domain(cls, domain: str) -> list[str]:
        """Return all project names that have the given domain."""
        projects = []
        for project in cls.list_all_projects():
            store = cls(project=project)
            if domain in store.list_domains():
                projects.append(project)
        return sorted(projects)

    def set_with_domain_tracking(self, key: str, value: str) -> None:
        """Set a key and ensure its domain and project are registered."""
        self.set(key, value)
        if self._domain:
            self.register_domain(self._domain)
        project_name = self._service.removeprefix(f"{self.prefix}:")
        self.register_global_project(project_name)

    def set_with_tracking(self, key: str, value: str) -> None:
        """Bridge to set_with_domain_tracking for the unified API."""
        self.set_with_domain_tracking(key, value)

    def delete_with_tracking(self, key: str) -> None:
        """Delete and update keyring-based registry."""
        self.delete(key)

    def clear_metadata(self) -> None:
        """Keychain metadata is cleaned up automatically via register/unregister."""

    def rebuild_registry(self) -> dict[str, list[str]]:
        """Rebuild is not needed for keychain (managed via manifests)."""
        return {}
