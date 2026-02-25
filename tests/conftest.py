"""Shared fixtures for enveloper tests."""

from __future__ import annotations

import pytest


@pytest.fixture()
def mock_keyring(monkeypatch: pytest.MonkeyPatch) -> dict[tuple[str, str], str]:
    """Replace the real keyring backend with an in-memory dict.

    Returns the backing dict so tests can inspect it directly.
    """
    store: dict[tuple[str, str], str] = {}

    def _get(service: str, username: str) -> str | None:
        return store.get((service, username))

    def _set(service: str, username: str, password: str) -> None:
        store[(service, username)] = password

    def _delete(service: str, username: str) -> None:
        key = (service, username)
        if key not in store:
            import keyring.errors

            raise keyring.errors.PasswordDeleteError(username)
        del store[key]

    monkeypatch.setattr("keyring.get_password", _get)
    monkeypatch.setattr("keyring.set_password", _set)
    monkeypatch.setattr("keyring.delete_password", _delete)

    return store


@pytest.fixture()
def sample_env(tmp_path):
    """Create a sample .env file and return its path."""
    content = """\
# AWS Config
AWS_PROFILE=default

TWILIO_API_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN="my secret token"
export MESSAGING_PROVIDER=twilio

# Quoted values
SINGLE_QUOTED='hello world'
INLINE_COMMENT=some_value # this is a comment
EMPTY_VALUE=
EQUALS_IN_VALUE=postgres://user:pass@host/db?opt=1
"""
    p = tmp_path / ".env"
    p.write_text(content)
    return p
