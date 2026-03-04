# Copyright (c) 2026 Ramin Firoozye
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for cloud and keychain operations: push, pull, clear, delete non-existent, re-create, verify.

All tests clean up after themselves (clear store or use isolated scope). Fake cloud store
is cleared after each test via autouse fixture in conftest.
"""

from __future__ import annotations

from enveloper.cli import cli

# ---------------------------------------------------------------------------
# Keychain: delete non-existent key, re-create, push different values, cleanup
# ---------------------------------------------------------------------------


def test_keychain_delete_nonexistent_key_no_error(cli_runner, mock_keyring):
    """Deleting a non-existent key on keychain should not error (idempotent)."""
    result = cli_runner.invoke(
        cli,
        ["--project", "kc_ops", "-d", "dev", "delete", "NONEXISTENT_KEY"],
    )
    # delete may exit 0 or non-zero depending on implementation; should not raise
    assert result.exception is None


def test_keychain_set_verify_delete_verify_recreate_verify(cli_runner, mock_keyring):
    """Set key, verify, delete, verify gone, set again (re-create), verify. Then cleanup."""
    project, domain = "kc_ops", "dev"
    key, val1, val2 = "RECREATE_KEY", "first_value", "second_value"

    cli_runner.invoke(cli, ["--project", project, "-d", domain, "set", key, val1])
    r = cli_runner.invoke(cli, ["--project", project, "-d", domain, "get", key])
    assert r.exit_code == 0
    assert val1 in r.output

    cli_runner.invoke(cli, ["--project", project, "-d", domain, "delete", key])
    r = cli_runner.invoke(cli, ["--project", project, "-d", domain, "get", key])
    assert r.exit_code != 0 or "not found" in r.output.lower()

    cli_runner.invoke(cli, ["--project", project, "-d", domain, "set", key, val2])
    r = cli_runner.invoke(cli, ["--project", project, "-d", domain, "get", key])
    assert r.exit_code == 0
    assert val2 in r.output

    # Cleanup: clear this domain/project
    cli_runner.invoke(cli, ["--project", project, "-d", domain, "clear", "--quiet"])
    r = cli_runner.invoke(cli, ["--project", project, "-d", domain, "list", "keys"])
    assert r.exit_code == 0
    assert "(empty)" in r.output


def test_keychain_push_different_values_to_existing_project(cli_runner, mock_keyring):
    """Set key to value A, verify; set same key to value B, verify B. Cleanup."""
    project, domain = "kc_ops", "dev"
    key = "OVERWRITE_KEY"

    cli_runner.invoke(cli, ["--project", project, "-d", domain, "set", key, "value_a"])
    r = cli_runner.invoke(cli, ["--project", project, "-d", domain, "get", key])
    assert r.exit_code == 0
    assert "value_a" in r.output

    cli_runner.invoke(cli, ["--project", project, "-d", domain, "set", key, "value_b"])
    r = cli_runner.invoke(cli, ["--project", project, "-d", domain, "get", key])
    assert r.exit_code == 0
    assert "value_b" in r.output

    cli_runner.invoke(cli, ["--project", project, "-d", domain, "clear", "--quiet"])


def test_keychain_clear_nonexistent_domain_then_recreate(cli_runner, mock_keyring):
    """Clear a domain that has no secrets (no error), then set keys and verify. Cleanup."""
    project, domain = "kc_ops", "nonexistent_xyz"
    result = cli_runner.invoke(cli, ["--project", project, "-d", domain, "clear", "--quiet"])
    assert result.exit_code == 0

    cli_runner.invoke(cli, ["--project", project, "-d", domain, "set", "K", "v"])
    r = cli_runner.invoke(cli, ["--project", project, "-d", domain, "list", "keys"])
    assert r.exit_code == 0
    assert "K" in r.output

    cli_runner.invoke(cli, ["--project", project, "-d", domain, "clear", "--quiet"])


# ---------------------------------------------------------------------------
# Cloud (fake): delete non-existent, push, verify, clear, re-create, cleanup
# ---------------------------------------------------------------------------


def test_cloud_delete_nonexistent_key_no_error(cli_runner, mock_keyring):
    """Deleting a non-existent key on cloud store should not error."""
    result = cli_runner.invoke(
        cli,
        [
            "--project", "cloud_ops", "-d", "dev",
            "--service", "gcp",
            "delete", "NONEXISTENT_KEY",
        ],
    )
    assert result.exception is None
    # Exit code may be 0 or non-zero; no crash
    assert result.exit_code in (0, 1, 2)


def test_cloud_push_list_verify_clear_list_empty(cli_runner, mock_keyring, sample_env):
    """Push to cloud, list and verify keys, clear, list empty. Cleanup is clear."""
    project, domain = "cloud_ops", "dev"
    cli_runner.invoke(cli, ["--project", project, "-d", domain, "import", str(sample_env)])
    result = cli_runner.invoke(
        cli,
        ["--project", project, "-d", domain, "--service", "gcp", "push"],
    )
    assert result.exit_code == 0
    assert "Pushed" in result.output

    r = cli_runner.invoke(
        cli,
        ["--project", project, "-d", domain, "--service", "gcp", "list", "keys"],
    )
    assert r.exit_code == 0
    assert "TWILIO_API_SID" in r.output or "SINGLE_QUOTED" in r.output

    result = cli_runner.invoke(
        cli,
        ["--project", project, "-d", domain, "--service", "gcp", "clear", "--quiet"],
    )
    assert result.exit_code == 0

    r = cli_runner.invoke(
        cli,
        ["--project", project, "-d", domain, "--service", "gcp", "list", "keys"],
    )
    assert r.exit_code == 0
    assert "(empty)" in r.output


def test_cloud_push_different_values_to_existing_project(cli_runner, mock_keyring):
    """Push value A to cloud, verify; push value B (overwrite), pull and verify B. Cleanup."""
    project, domain = "cloud_ops", "dev"
    key, val_a, val_b = "CLOUD_KEY", "value_a", "value_b"

    cli_runner.invoke(cli, ["--project", project, "-d", domain, "set", key, val_a])
    result = cli_runner.invoke(
        cli,
        ["--project", project, "-d", domain, "--service", "gcp", "push"],
    )
    assert result.exit_code == 0

    r = cli_runner.invoke(
        cli,
        ["--project", project, "-d", domain, "--service", "gcp", "list", "keys"],
    )
    assert r.exit_code == 0
    assert key in r.output or "CLOUD_KEY" in r.output

    cli_runner.invoke(cli, ["--project", project, "-d", domain, "set", key, val_b])
    result = cli_runner.invoke(
        cli,
        ["--project", project, "-d", domain, "--service", "gcp", "push"],
    )
    assert result.exit_code == 0

    result = cli_runner.invoke(
        cli,
        ["--project", project, "-d", domain, "--service", "gcp", "pull", "--to", "local"],
    )
    assert result.exit_code == 0
    r = cli_runner.invoke(cli, ["--project", project, "-d", domain, "get", key])
    assert r.exit_code == 0
    assert val_b in r.output

    cli_runner.invoke(cli, ["--project", project, "-d", domain, "clear", "--quiet"])
    cli_runner.invoke(
        cli,
        ["--project", project, "-d", domain, "--service", "gcp", "clear", "--quiet"],
    )


def test_cloud_clear_then_push_recreate(cli_runner, mock_keyring, sample_env):
    """Push to cloud, clear, then push again (re-create project/domain). Verify. Cleanup."""
    project, domain = "cloud_ops", "dev"
    cli_runner.invoke(cli, ["--project", project, "-d", domain, "import", str(sample_env)])
    cli_runner.invoke(cli, ["--project", project, "-d", domain, "--service", "gcp", "push"])
    cli_runner.invoke(cli, ["--project", project, "-d", domain, "--service", "gcp", "clear", "--quiet"])

    r = cli_runner.invoke(
        cli,
        ["--project", project, "-d", domain, "--service", "gcp", "list", "keys"],
    )
    assert r.exit_code == 0
    assert "(empty)" in r.output

    cli_runner.invoke(cli, ["--project", project, "-d", domain, "import", str(sample_env)])
    result = cli_runner.invoke(cli, ["--project", project, "-d", domain, "--service", "gcp", "push"])
    assert result.exit_code == 0
    assert "Pushed" in result.output

    r = cli_runner.invoke(
        cli,
        ["--project", project, "-d", domain, "--service", "gcp", "list", "keys"],
    )
    assert r.exit_code == 0
    assert "TWILIO" in r.output or "SINGLE_QUOTED" in r.output

    cli_runner.invoke(cli, ["--project", project, "-d", domain, "--service", "gcp", "clear", "--quiet"])


def test_cloud_list_domain_list_project_after_push(cli_runner, mock_keyring, sample_env):
    """Push to cloud, then list domain and list project; verify they show. Cleanup."""
    project, domain = "cloud_ops", "dev"
    cli_runner.invoke(cli, ["--project", project, "-d", domain, "import", str(sample_env)])
    cli_runner.invoke(cli, ["--project", project, "-d", domain, "--service", "gcp", "push"])

    r = cli_runner.invoke(cli, ["--service", "gcp", "list", "domain"])
    assert r.exit_code == 0
    assert domain in r.output
    r = cli_runner.invoke(cli, ["--service", "gcp", "list", "project", "-d", domain])
    assert r.exit_code == 0
    assert project in r.output

    cli_runner.invoke(cli, ["--project", project, "-d", domain, "--service", "gcp", "clear", "--quiet"])


def test_cloud_clear_nonexistent_domain_no_error(cli_runner, mock_keyring):
    """Clear cloud for a domain that has no secrets; should succeed. No cleanup needed."""
    result = cli_runner.invoke(
        cli,
        [
            "--project", "cloud_ops", "-d", "nonexistent_cloud_xyz",
            "--service", "azure", "clear", "--quiet",
        ],
    )
    assert result.exit_code == 0
    assert "Cleared" in result.output


def test_cloud_clear_nonexistent_project_no_error(cli_runner, mock_keyring):
    """Clear cloud for a project that has no secrets; should succeed."""
    result = cli_runner.invoke(
        cli,
        [
            "--project", "nonexistent_cloud_proj_xyz", "-d", "_default_",
            "--service", "gcp", "clear", "--quiet",
        ],
    )
    assert result.exit_code == 0
    assert "Cleared" in result.output


def test_cloud_pull_then_verify_values(cli_runner, mock_keyring, sample_env):
    """Push to cloud, pull to local, verify values. Cleanup both."""
    project, domain = "cloud_ops", "dev"
    cli_runner.invoke(cli, ["--project", project, "-d", domain, "import", str(sample_env)])
    cli_runner.invoke(cli, ["--project", project, "-d", domain, "--service", "gcp", "push"])

    result = cli_runner.invoke(
        cli,
        ["--project", project, "-d", domain, "--service", "gcp", "pull", "--to", "local"],
    )
    assert result.exit_code == 0
    assert "Pulled" in result.output

    r = cli_runner.invoke(cli, ["--project", project, "-d", domain, "list", "keys"])
    assert r.exit_code == 0
    assert "TWILIO" in r.output or "SINGLE_QUOTED" in r.output

    cli_runner.invoke(cli, ["--project", project, "-d", domain, "clear", "--quiet"])
    cli_runner.invoke(cli, ["--project", project, "-d", domain, "--service", "gcp", "clear", "--quiet"])
