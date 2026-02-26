"""KeychainStore -- local secret storage via the ``keyring`` library.

Cross-platform: macOS Keychain, Linux SecretService (GNOME Keyring / KDE
Wallet), Windows Credential Locker.

Secrets are stored under service ``enveloper:{project}`` with username
``{domain}/{key}``.  A manifest entry at ``{domain}/__keys__`` holds a
JSON list of key names so we can enumerate without scanning the whole
keychain.
"""

from __future__ import annotations

import json

import keyring

from enveloper.store import SecretStore

_MANIFEST_KEY = "__keys__"


class KeychainStore(SecretStore):
    """Read/write secrets in the OS keychain, scoped by project and domain."""

    def __init__(self, project: str = "_default_", domain: str | None = None) -> None:
        self._service = f"enveloper:{project}"
        self._domain = domain

    def _username(self, key: str) -> str:
        if self._domain:
            return f"{self._domain}/{key}"
        return key

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

    def set_with_domain_tracking(self, key: str, value: str) -> None:
        """Set a key and ensure its domain is registered in the domain manifest."""
        self.set(key, value)
        if self._domain:
            self.register_domain(self._domain)
