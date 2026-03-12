# Copyright (c) 2026 Ramin Firoozye
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Reusable input validation and sanitization helpers."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

MAX_ENV_KEY_LENGTH = 255
MAX_ENV_ENTRY_LENGTH = 32767
MAX_FILE_PATH_LENGTH = 4096

_ENV_KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_NAMESPACE_SEGMENT_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
_ABSOLUTE_WINDOWS_PATH_RE = re.compile(r"^(?:[A-Za-z]:[\\/]|\\\\)")

_SUSPICIOUS_SQL_RE = re.compile(
    r"(?ix)"
    r"(?:'\s*or\s+['\"]?1['\"]?\s*=\s*['\"]?1)"
    r"|(?:union\s+select)"
    r"|(?:;\s*(?:drop|truncate|delete|update|insert)\b)"
)
_SUSPICIOUS_SHELL_RE = re.compile(
    r"(?x)"
    r"(?:`[^`]*`)"
    r"|(?:\$\([^)]*\))"
    r"|(?:&&|\|\|)"
    r"|(?:;\s*[A-Za-z0-9_./-])"
    r"|(?:\|\s*[A-Za-z0-9_./-])"
)
_SUSPICIOUS_PROMPT_RE = re.compile(
    r"(?ix)"
    r"(?:ignore\s+(?:all\s+)?previous\s+instructions)"
    r"|(?:system\s+prompt)"
    r"|(?:developer\s+message)"
    r"|(?:prompt\s+injection)"
    r"|(?:jailbreak)"
    r"|(?:<\|\s*(?:system|assistant|user)\s*\|>)"
)
_SUSPICIOUS_PATH_SHELL_RE = re.compile(r"[;&|<>`]")
_SUSPICIOUS_WINDOWS_ESCAPE_RE = re.compile(r"(?:%[A-Za-z0-9_]+%|\^)")


class SanitizationError(ValueError):
    """Raised when a key, value, or file path fails validation."""


def _ensure_text(value: str, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise SanitizationError(f"{field_name} must be a string.")
    try:
        value.encode("utf-8", "strict")
    except UnicodeEncodeError as exc:
        raise SanitizationError(f"{field_name} contains invalid unicode.") from exc
    return value


def _ensure_no_compatibility_variants(value: str, *, field_name: str) -> None:
    if unicodedata.normalize("NFKC", value) != value:
        raise SanitizationError(
            f"{field_name} contains unicode compatibility characters or punctuation variants."
        )


def _ensure_no_controls(value: str, *, field_name: str, allow_newlines: bool = False) -> None:
    allowed = {"\n", "\r", "\t"} if allow_newlines else set()
    for char in value:
        if char in allowed:
            continue
        if unicodedata.category(char).startswith("C"):
            raise SanitizationError(f"{field_name} contains control characters.")


def _ensure_safe_length(value: str, *, field_name: str, limit: int) -> None:
    if len(value) > limit:
        raise SanitizationError(f"{field_name} exceeds the maximum supported length of {limit} characters.")


def _check_injection_patterns(value: str, *, field_name: str) -> None:
    if _SUSPICIOUS_SQL_RE.search(value):
        raise SanitizationError(f"{field_name} contains a suspicious SQL injection pattern.")
    if _SUSPICIOUS_SHELL_RE.search(value):
        raise SanitizationError(f"{field_name} contains a suspicious shell injection pattern.")
    if _SUSPICIOUS_PROMPT_RE.search(value):
        raise SanitizationError(f"{field_name} contains a suspicious prompt injection pattern.")


def sanitize_secret_key(key: str) -> str:
    """Validate a secret key for cross-platform env-var compatibility."""
    key = _ensure_text(key, field_name="key")
    if not key:
        raise SanitizationError("key cannot be empty.")
    _ensure_safe_length(key, field_name="key", limit=MAX_ENV_KEY_LENGTH)
    _ensure_no_controls(key, field_name="key")
    _ensure_no_compatibility_variants(key, field_name="key")
    if not _ENV_KEY_RE.fullmatch(key):
        raise SanitizationError(
            "key must start with a letter or underscore and contain only ASCII letters, digits, and underscores."
        )
    return key


def sanitize_namespace_segment(value: str, *, default: str, field_name: str) -> str:
    """Validate a store namespace segment such as domain or project."""
    value = _ensure_text(value, field_name=field_name).strip()
    if not value:
        return default
    _ensure_safe_length(value, field_name=field_name, limit=MAX_ENV_KEY_LENGTH)
    _ensure_no_controls(value, field_name=field_name)
    _ensure_no_compatibility_variants(value, field_name=field_name)
    _check_injection_patterns(value, field_name=field_name)
    if not _NAMESPACE_SEGMENT_RE.fullmatch(value):
        raise SanitizationError(
            f"{field_name} must contain only ASCII letters, digits, underscores, hyphens, or dots."
        )
    return value


def max_value_length_for_key(key: str) -> int:
    return MAX_ENV_ENTRY_LENGTH - len(key) - 1


def sanitize_secret_value(value: str, *, key: str | None = None) -> str:
    """Validate a secret value for length and common injection payloads."""
    value = _ensure_text(value, field_name="value")
    _ensure_no_controls(value, field_name="value", allow_newlines=True)
    limit = max_value_length_for_key(key or "")
    _ensure_safe_length(value, field_name="value", limit=limit)
    _check_injection_patterns(value, field_name="value")
    return value


def sanitize_secret_pair(key: str, value: str) -> tuple[str, str]:
    """Validate a key/value pair before persisting or exporting it."""
    key = sanitize_secret_key(key)
    value = sanitize_secret_value(value, key=key)
    return key, value


def sanitize_file_access_path(path: str | Path) -> Path:
    """Validate a file path before reading or writing it."""
    raw_path = _ensure_text(str(path), field_name="path").strip()
    if not raw_path:
        raise SanitizationError("path cannot be empty.")
    _ensure_safe_length(raw_path, field_name="path", limit=MAX_FILE_PATH_LENGTH)
    _ensure_no_controls(raw_path, field_name="path")
    _ensure_no_compatibility_variants(raw_path, field_name="path")
    _check_injection_patterns(raw_path, field_name="path")
    if _SUSPICIOUS_PATH_SHELL_RE.search(raw_path) or _SUSPICIOUS_WINDOWS_ESCAPE_RE.search(raw_path):
        raise SanitizationError("path contains shell escape characters.")
    candidate = Path(raw_path)
    if raw_path in {"/", "\\\\"} or _ABSOLUTE_WINDOWS_PATH_RE.fullmatch(raw_path):
        raise SanitizationError("root-only absolute paths are not allowed.")
    if ".." in candidate.parts:
        raise SanitizationError("path traversal is not allowed.")
    if "../" in raw_path or "..\\" in raw_path:
        raise SanitizationError("path traversal is not allowed.")
    return candidate
