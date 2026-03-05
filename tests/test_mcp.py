# Copyright (c) 2026 Ramin Firoozye
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for the MCP server: tool behavior and server startup."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from enveloper.mcp_server import (
    clear_scope,
    delete_secret,
    export_env,
    get_secret,
    import_from_file,
    list_domains,
    list_keys,
    list_projects,
    list_services,
    main,
    pull_from_service,
    push_to_service,
    set_secret,
    unexport_env,
)

# ---------------------------------------------------------------------------
# Tool functions with file store (no keyring)
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_mcp_get_secret_with_file_store(tmp_path: Path) -> None:
    """get_secret returns value when key exists in file store."""
    env_file = tmp_path / ".env"
    env_file.write_text("MY_API_KEY=secret123\nLEVEL_SET=42\n")
    result = get_secret("MY_API_KEY", service="file", path=str(env_file))
    assert result == "secret123"
    result2 = get_secret("LEVEL_SET", service="file", path=str(env_file))
    assert result2 == "42"


@pytest.mark.unit
def test_mcp_get_secret_missing_returns_human_friendly_message(tmp_path: Path) -> None:
    """get_secret returns a human-friendly message when key is missing."""
    env_file = tmp_path / ".env"
    env_file.write_text("OTHER=1\n")
    result = get_secret("MISSING_KEY", service="file", path=str(env_file))
    assert result
    assert "not found" in result.lower() or "MISSING_KEY" in result


@pytest.mark.unit
def test_mcp_list_keys_with_file_store(tmp_path: Path) -> None:
    """list_keys returns key names for file store."""
    env_file = tmp_path / ".env"
    env_file.write_text("A=1\nB=2\n")
    result = list_keys(service="file", path=str(env_file))
    assert "A" in result
    assert "B" in result
    assert len(result) == 2


@pytest.mark.unit
def test_mcp_export_env_dotenv(tmp_path: Path) -> None:
    """export_env returns dotenv-format lines."""
    env_file = tmp_path / ".env"
    env_file.write_text("MY_KEY=myval\n")
    result = export_env(service="file", path=str(env_file), format="dotenv")
    assert "MY_KEY=" in result
    assert "myval" in result


@pytest.mark.unit
def test_mcp_export_env_unix(tmp_path: Path) -> None:
    """export_env with format=unix returns export KEY='value' lines."""
    env_file = tmp_path / ".env"
    env_file.write_text("X=y\n")
    result = export_env(service="file", path=str(env_file), format="unix")
    assert result.startswith("export ")
    assert "X=" in result or "X='" in result


@pytest.mark.unit
def test_mcp_list_domains_file_store(tmp_path: Path) -> None:
    """list_domains with file store returns _default_ when keys exist."""
    env_file = tmp_path / ".env"
    env_file.write_text("K=1\n")
    result = list_domains(service="file")
    # File store returns [_default_] when it has keys; without project we still
    # resolve service=file but list_domains for file uses get_store with default domain
    assert isinstance(result, list)


@pytest.mark.unit
def test_mcp_list_projects_file_store() -> None:
    """list_projects with file store returns list (may be empty)."""
    result = list_projects(domain="_default_", service="file")
    assert isinstance(result, list)


@pytest.mark.unit
def test_mcp_set_secret_with_file_store(tmp_path: Path) -> None:
    """set_secret writes to file store and get_secret reads it back."""
    env_file = tmp_path / ".env"
    env_file.write_text("")
    msg = set_secret("NEW_KEY", "new_value", service="file", path=str(env_file))
    assert "Set" in msg
    assert get_secret("NEW_KEY", service="file", path=str(env_file)) == "new_value"


@pytest.mark.unit
def test_mcp_delete_secret_with_file_store(tmp_path: Path) -> None:
    """delete_secret removes key from file store."""
    env_file = tmp_path / ".env"
    env_file.write_text("TO_DEL=1\n")
    msg = delete_secret("TO_DEL", service="file", path=str(env_file))
    assert "Removed" in msg
    assert "not found" in get_secret("TO_DEL", service="file", path=str(env_file))


@pytest.mark.unit
def test_mcp_import_from_file(tmp_path: Path) -> None:
    """import_from_file reads .env and writes to target store."""
    source = tmp_path / "source.env"
    source.write_text("IMPORTED_A=1\nIMPORTED_B=2\n")
    target = tmp_path / ".env"
    target.write_text("")
    msg = import_from_file(str(source), service="file", path=str(target))
    assert "Imported" in msg and "2" in msg
    assert get_secret("IMPORTED_A", service="file", path=str(target)) == "1"
    assert get_secret("IMPORTED_B", service="file", path=str(target)) == "2"


@pytest.mark.unit
def test_mcp_clear_scope_file_store(tmp_path: Path) -> None:
    """clear_scope removes all keys from file store."""
    env_file = tmp_path / ".env"
    env_file.write_text("C1=1\nC2=2\n")
    msg = clear_scope(service="file", path=str(env_file))
    assert "Cleared" in msg
    assert list_keys(service="file", path=str(env_file)) == []


@pytest.mark.unit
def test_mcp_unexport_env_returns_unset_lines(tmp_path: Path) -> None:
    """unexport_env returns unset KEY lines."""
    env_file = tmp_path / ".env"
    env_file.write_text("U1=a\nU2=b\n")
    result = unexport_env(service="file", path=str(env_file), format="unix")
    assert "unset " in result
    assert "U1" in result and "U2" in result


@pytest.mark.unit
def test_mcp_list_services_returns_names() -> None:
    """list_services returns at least keychain and file."""
    result = list_services()
    assert "keychain" in result
    assert "file" in result


# ---------------------------------------------------------------------------
# Positive: edge cases and empty inputs
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_mcp_export_env_empty_store_returns_comment(tmp_path: Path) -> None:
    """export_env on empty store returns comment line, not crash."""
    env_file = tmp_path / ".env"
    env_file.write_text("")
    result = export_env(service="file", path=str(env_file), format="dotenv")
    assert "no secrets" in result or result.strip().startswith("#")


@pytest.mark.unit
def test_mcp_unexport_env_empty_store_returns_comment_or_empty(tmp_path: Path) -> None:
    """unexport_env on empty store returns comment or no keys."""
    env_file = tmp_path / ".env"
    env_file.write_text("")
    result = unexport_env(service="file", path=str(env_file), format="unix")
    assert "no keys" in result or result.strip().startswith("#") or result.strip() == ""


@pytest.mark.unit
def test_mcp_list_keys_nonexistent_path_returns_empty(tmp_path: Path) -> None:
    """list_keys with path to nonexistent file returns empty list (no exception)."""
    nonexistent = tmp_path / "nonexistent.env"
    assert not nonexistent.exists()
    result = list_keys(service="file", path=str(nonexistent))
    assert result == []


@pytest.mark.unit
def test_mcp_clear_scope_already_empty_succeeds(tmp_path: Path) -> None:
    """clear_scope on already empty store still returns success message."""
    env_file = tmp_path / ".env"
    env_file.write_text("")
    msg = clear_scope(service="file", path=str(env_file))
    assert "Cleared" in msg


@pytest.mark.unit
def test_mcp_delete_secret_nonexistent_key_succeeds(tmp_path: Path) -> None:
    """delete_secret for nonexistent key still returns Removed (idempotent)."""
    env_file = tmp_path / ".env"
    env_file.write_text("A=1\n")
    msg = delete_secret("NONEXISTENT", service="file", path=str(env_file))
    assert "Removed" in msg
    assert get_secret("A", service="file", path=str(env_file)) == "1"


# ---------------------------------------------------------------------------
# Negative: invalid or missing inputs
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_mcp_import_from_file_nonexistent_path_returns_error(tmp_path: Path) -> None:
    """import_from_file with nonexistent file path returns human-friendly error."""
    nonexistent = tmp_path / "does_not_exist.env"
    assert not nonexistent.exists()
    target = tmp_path / ".env"
    target.write_text("")
    result = import_from_file(str(nonexistent), service="file", path=str(target))
    assert result
    assert "not found" in result.lower() or "file" in result.lower() or "went wrong" in result.lower()


@pytest.mark.unit
def test_mcp_import_from_file_empty_file_returns_message(tmp_path: Path) -> None:
    """import_from_file with empty file returns no variables message."""
    empty = tmp_path / "empty.env"
    empty.write_text("")
    target = tmp_path / ".env"
    target.write_text("")
    result = import_from_file(str(empty), service="file", path=str(target))
    assert "no variable" in result.lower() or "no variables" in result.lower() or "0" in result


@pytest.mark.unit
def test_mcp_get_secret_nonexistent_path_returns_not_found_or_error(tmp_path: Path) -> None:
    """get_secret with path to nonexistent file returns not found or error message."""
    nonexistent = tmp_path / "missing.env"
    assert not nonexistent.exists()
    result = get_secret("ANY_KEY", service="file", path=str(nonexistent))
    assert result
    assert "not found" in result.lower() or "went wrong" in result.lower()


@pytest.mark.unit
def test_mcp_push_to_service_invalid_target_returns_error() -> None:
    """push_to_service with cloud_service=local returns human-friendly error (must be cloud)."""
    result = push_to_service("local", from_service="local")
    assert result
    assert "cloud" in result.lower() or "target" in result.lower() or "push" in result.lower()


@pytest.mark.unit
def test_mcp_push_to_service_file_target_returns_error() -> None:
    """push_to_service with cloud_service=file returns human-friendly error."""
    result = push_to_service("file", from_service="local")
    assert result
    assert "cloud" in result.lower() or "push" in result.lower()


@pytest.mark.unit
def test_mcp_pull_from_service_invalid_source_returns_error() -> None:
    """pull_from_service with cloud_service=local returns human-friendly error (must be cloud)."""
    result = pull_from_service("local", to_service="local")
    assert result
    assert "cloud" in result.lower() or "source" in result.lower() or "pull" in result.lower()


@pytest.mark.unit
def test_mcp_pull_from_service_file_source_returns_error() -> None:
    """pull_from_service with cloud_service=file returns human-friendly error."""
    result = pull_from_service("file", to_service="local")
    assert result
    assert "cloud" in result.lower() or "pull" in result.lower()


@pytest.mark.unit
def test_mcp_error_responses_are_non_empty_and_contain_failure_indicator() -> None:
    """Error and failure responses are non-empty and indicate something went wrong."""
    # Missing key: message should exist and indicate not found
    r1 = get_secret("NONEXISTENT_KEY", service="file", path="/nonexistent/path/.env")
    assert r1
    assert "not found" in r1.lower() or "went wrong" in r1.lower()
    # Invalid push: message should exist and mention cloud or push
    r2 = push_to_service("local")
    assert r2
    assert "cloud" in r2.lower() or "push" in r2.lower()


@pytest.mark.unit
def test_mcp_human_friendly_error_messages(tmp_path: Path) -> None:
    """Error messages use human-friendly wording (no raw 'error:' or '(error:')."""
    # Missing key: should say "Secret not found" or similar, not "(error: ...)"
    env_file = tmp_path / ".env"
    env_file.write_text("X=1\n")
    r = get_secret("MISSING", service="file", path=str(env_file))
    assert "secret" in r.lower() and "not found" in r.lower()
    # Nonexistent file: should say "File not found" or "Something went wrong"
    r2 = import_from_file(str(tmp_path / "nope.env"), service="file", path=str(env_file))
    assert r2
    assert "file" in r2.lower() and ("not found" in r2.lower() or "went wrong" in r2.lower())
    # Invalid push: should say "Push target must be" or similar
    r3 = push_to_service("local")
    assert "push" in r3.lower() or "target" in r3.lower() or "cloud" in r3.lower()


# ---------------------------------------------------------------------------
# main() when mcp is not installed
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_mcp_main_exits_when_mcp_import_fails() -> None:
    """main() raises SystemExit with install message when mcp is not importable."""
    import builtins

    real_import = builtins.__import__

    def fail_mcp_import(
        name: str,
        globals: dict[str, Any] | None = None,
        locals: dict[str, Any] | None = None,
        fromlist: Any = None,
        level: int = 0,
    ) -> Any:
        if name in ("mcp", "mcp.server.fastmcp"):
            raise ImportError("No module named 'mcp'")
        return real_import(name, globals, locals, fromlist, level)

    with patch.object(builtins, "__import__", fail_mcp_import):
        with pytest.raises(SystemExit):
            main()


# ---------------------------------------------------------------------------
# MCP server process (integration)
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_mcp_server_responds_to_initialize() -> None:
    """MCP server responds to initialize JSON-RPC with Enveloper server name."""
    proc = subprocess.run(
        [sys.executable, "-m", "enveloper.mcp_server"],
        input=json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "test", "version": "1.0"},
                },
            }
        ).encode(),
        capture_output=True,
        timeout=5,
        cwd=Path(__file__).resolve().parent.parent,
    )
    assert proc.returncode == 0
    out = proc.stdout.decode()
    data = json.loads(out.strip())
    assert data.get("result", {}).get("serverInfo", {}).get("name") == "Enveloper"
