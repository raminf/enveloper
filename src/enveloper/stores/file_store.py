"""FileStore -- read/write secrets from a plain .env file.

Used when --service file (with optional --path, default .env).
"""

from __future__ import annotations

from pathlib import Path

from enveloper.env_file import parse_env_file
from enveloper.store import SecretStore


def _format_env_value(value: str) -> str:
    """Format a value for .env: quote if needed."""
    if not value:
        return '""'
    if "\n" in value or "\r" in value or '"' in value or " " in value or "=" in value:
        return '"' + value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'
    return value


class FileStore(SecretStore):
    """Read/write secrets as key-value pairs in a single .env file."""

    service_name: str = "file"
    service_display_name: str = "Plain .env file"
    service_doc_url: str = "https://github.com/motdotla/dotenv"

    key_separator: str = "/"

    def __init__(self, path: str | Path = ".env") -> None:
        self._path = Path(path)

    def _read(self) -> dict[str, str]:
        if not self._path.is_file():
            return {}
        return parse_env_file(self._path)

    def _write(self, data: dict[str, str]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        lines = [f"{k}={_format_env_value(v)}" for k, v in sorted(data.items())]
        self._path.write_text("\n".join(lines) + "\n" if lines else "")

    def get(self, key: str) -> str | None:
        return self._read().get(key)

    def set(self, key: str, value: str) -> None:
        data = self._read()
        data[key] = value
        self._write(data)

    def delete(self, key: str) -> None:
        data = self._read()
        if key in data:
            del data[key]
            self._write(data)

    def list_keys(self) -> list[str]:
        return sorted(self._read().keys())

    def clear(self) -> None:
        self._write({})
