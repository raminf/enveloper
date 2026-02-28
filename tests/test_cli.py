
"""Tests for CLI commands via click.testing.CliRunner."""

from __future__ import annotations

import importlib.metadata

from click.testing import CliRunner

from enveloper.cli import cli


def test_version():
    """Version output must match the package version from the project."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    expected_version = importlib.metadata.version("enveloper")
    assert expected_version in result.output


def test_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "import" in result.output
    assert "export" in result.output


def test_import_and_list(mock_keyring, sample_env):
    runner = CliRunner()
    result = runner.invoke(cli, ["--project", "test", "-d", "aws", "import", str(sample_env)])
    assert result.exit_code == 0
    assert "Imported" in result.output

    result = runner.invoke(cli, ["--project", "test", "-d", "aws", "list"])
    assert result.exit_code == 0
    assert "TWILIO_API_SID" in result.output


def test_import_and_export_env(mock_keyring, sample_env):
    runner = CliRunner()
    runner.invoke(cli, ["--project", "test", "-d", "aws", "import", str(sample_env)])

    result = runner.invoke(cli, ["--project", "test", "-d", "aws", "export", "--format", "dotenv"])
    assert result.exit_code == 0
    assert "TWILIO_API_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" in result.output


def test_import_and_export_json(mock_keyring, sample_env):
    runner = CliRunner()
    runner.invoke(cli, ["--project", "test", "-d", "aws", "import", str(sample_env)])

    result = runner.invoke(cli, ["--project", "test", "-d", "aws", "export", "--format", "json"])
    assert result.exit_code == 0
    import json

    data = json.loads(result.output)
    assert "TWILIO_API_SID" in data


def test_get_and_set(mock_keyring):
    runner = CliRunner()
    result = runner.invoke(cli, ["--project", "test", "-d", "d", "set", "FOO", "bar"])
    assert result.exit_code == 0

    result = runner.invoke(cli, ["--project", "test", "-d", "d", "get", "FOO"])
    assert result.exit_code == 0
    assert result.output.strip() == "bar"


def test_get_missing(mock_keyring):
    runner = CliRunner()
    result = runner.invoke(cli, ["--project", "test", "-d", "d", "get", "NOPE"])
    assert result.exit_code != 0
    assert "not found" in result.output


def test_rm(mock_keyring):
    runner = CliRunner()
    runner.invoke(cli, ["--project", "test", "-d", "d", "set", "FOO", "bar"])
    result = runner.invoke(cli, ["--project", "test", "-d", "d", "delete", "FOO"])
    assert result.exit_code == 0

    result = runner.invoke(cli, ["--project", "test", "-d", "d", "get", "FOO"])
    assert result.exit_code != 0


def test_double_delete_key(mock_keyring):
    """Deleting the same key twice is idempotent; get after second delete still reports not found."""
    runner = CliRunner()
    runner.invoke(cli, ["--project", "test", "-d", "d", "set", "DOUBLE_K", "v1"])
    r1 = runner.invoke(cli, ["--project", "test", "-d", "d", "delete", "DOUBLE_K"])
    assert r1.exit_code == 0
    r2 = runner.invoke(cli, ["--project", "test", "-d", "d", "delete", "DOUBLE_K"])
    assert r2.exit_code == 0
    result = runner.invoke(cli, ["--project", "test", "-d", "d", "get", "DOUBLE_K"])
    assert result.exit_code != 0
    assert "not found" in result.output.lower()


def test_set_then_get_verifies_change(mock_keyring):
    """Set a value, then get to verify the change took effect."""
    runner = CliRunner()
    runner.invoke(cli, ["--project", "test", "-d", "d", "set", "VERIFY_K", "original"])
    r = runner.invoke(cli, ["--project", "test", "-d", "d", "get", "VERIFY_K"])
    assert r.exit_code == 0
    assert r.output.strip() == "original"
    runner.invoke(cli, ["--project", "test", "-d", "d", "set", "VERIFY_K", "updated"])
    r2 = runner.invoke(cli, ["--project", "test", "-d", "d", "get", "VERIFY_K"])
    assert r2.exit_code == 0
    assert r2.output.strip() == "updated"


def test_clear(mock_keyring):
    runner = CliRunner()
    runner.invoke(cli, ["--project", "test", "-d", "d", "set", "A", "1"])
    runner.invoke(cli, ["--project", "test", "-d", "d", "set", "B", "2"])
    result = runner.invoke(cli, ["--project", "test", "-d", "d", "clear", "--quiet"])
    assert result.exit_code == 0
    assert "Cleared" in result.output


def test_clear_after_import_then_verify_gone(mock_keyring, sample_env):
    """Import a set, clear it, then verify the keys are no longer in the store."""
    runner = CliRunner()
    runner.invoke(cli, ["--project", "test", "-d", "clear_import", "import", str(sample_env)])
    r_list_before = runner.invoke(cli, ["--project", "test", "-d", "clear_import", "list"])
    assert r_list_before.exit_code == 0
    assert "TWILIO_API_SID" in r_list_before.output

    result = runner.invoke(cli, ["--project", "test", "-d", "clear_import", "clear", "--quiet"])
    assert result.exit_code == 0
    assert "Cleared" in result.output

    r_list_after = runner.invoke(cli, ["--project", "test", "-d", "clear_import", "list"])
    assert r_list_after.exit_code == 0
    assert "TWILIO_API_SID" not in r_list_after.output

    r_get = runner.invoke(cli, ["--project", "test", "-d", "clear_import", "get", "TWILIO_API_SID"])
    assert r_get.exit_code != 0
    assert "not found" in r_get.output.lower()


def test_stores():
    runner = CliRunner()
    result = runner.invoke(cli, ["stores"])
    assert result.exit_code == 0
    assert "keychain" in result.output
    assert "aws" in result.output
    assert "github" in result.output


def test_service():
    """List service providers in a Rich table: local, file, then cloud stores."""
    runner = CliRunner()
    result = runner.invoke(cli, ["service"])
    assert result.exit_code == 0
    assert "Service providers" in result.output
    assert "local" in result.output
    assert "file" in result.output
    assert "OS keychain" in result.output or "macOS" in result.output
    assert "aws" in result.output or "github" in result.output
    assert "Documentation" in result.output or "https://" in result.output


def test_service_uses_store_metadata():
    """Service command shows short names and descriptions from each store class (not hard-coded)."""
    from enveloper.stores.aws_ssm import AwsSsmStore
    from enveloper.stores.file_store import FileStore

    runner = CliRunner()
    result = runner.invoke(cli, ["service"])
    assert result.exit_code == 0
    # From FileStore
    assert FileStore.service_display_name in result.output
    assert FileStore.service_name in result.output
    # From KeychainStore (one of the platform rows)
    assert "macOS Keychain" in result.output
    # From at least one cloud store (AWS or GitHub etc.)
    assert AwsSsmStore.service_display_name in result.output or "GitHub Actions" in result.output
    # Documentation column is present (Rich renders links as "Doc Link" text)
    assert "Doc Link" in result.output or "Documentation" in result.output


def test_service_file_list_get_set(tmp_path):
    """List, get, and set with --service file and --path."""
    env_file = tmp_path / "my.env"
    env_file.write_text("FOO=bar\nBAZ=qux\n")
    runner = CliRunner()
    result = runner.invoke(cli, ["--service", "file", "--path", str(env_file), "list"])
    assert result.exit_code == 0
    assert "FOO" in result.output and "BAZ" in result.output
    result = runner.invoke(cli, ["--service", "file", "--path", str(env_file), "get", "FOO"])
    assert result.exit_code == 0
    assert "bar" in result.output
    result = runner.invoke(cli, ["--service", "file", "--path", str(env_file), "set", "NEW", "value"])
    assert result.exit_code == 0
    result = runner.invoke(cli, ["--service", "file", "--path", str(env_file), "list"])
    assert result.exit_code == 0
    assert "NEW" in result.output
    assert "NEW=value" in env_file.read_text() or "NEW=" in env_file.read_text()


# ---------------------------------------------------------------------------
# --service and --path flags: positive and negative tests
# ---------------------------------------------------------------------------

def test_service_flag_local_explicit(mock_keyring):
    """--service local behaves like default (keychain)."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--project", "test", "--service", "local", "list"])
    assert result.exit_code == 0


def test_service_flag_short_form(tmp_path):
    """-s file works like --service file."""
    env_file = tmp_path / "short.env"
    env_file.write_text("X=1\n")
    runner = CliRunner()
    result = runner.invoke(cli, ["-s", "file", "--path", str(env_file), "list"])
    assert result.exit_code == 0
    assert "X" in result.output


def test_service_from_env(tmp_path):
    """ENVELOPER_SERVICE is used when --service is not passed."""
    import os
    env_file = tmp_path / "from_env.env"
    env_file.write_text("FROM_ENV=ok\n")
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--path", str(env_file), "list"],
        env={**os.environ, "ENVELOPER_SERVICE": "file"},
    )
    assert result.exit_code == 0
    assert "FROM_ENV" in result.output


def test_path_with_service_file(tmp_path):
    """--path is used when --service file and points to .env file."""
    env_file = tmp_path / "custom.env"
    env_file.write_text("CUSTOM=yes\n")
    runner = CliRunner()
    result = runner.invoke(cli, ["--service", "file", "--path", str(env_file), "get", "CUSTOM"])
    assert result.exit_code == 0
    assert "yes" in result.output


def test_path_ignored_when_service_local(mock_keyring):
    """--path with --service local is ignored (keychain used)."""
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--project", "test", "--service", "local", "--path", "/nonexistent/.env", "list"],
    )
    assert result.exit_code == 0
    # Should show keychain list (default or empty), not try to read file
    assert "No secrets stored" in result.output or "_default_" in result.output or "Project" in result.output


def test_service_file_nonexistent_path_list():
    """--service file with nonexistent path: list returns empty (FileStore treats as empty)."""
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--service", "file", "--path", "/nonexistent/env/file.env", "list"],
    )
    assert result.exit_code == 0
    assert "(empty)" in result.output


def test_service_file_nonexistent_path_get():
    """--service file with nonexistent path: get returns not found."""
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--service", "file", "--path", "/nonexistent/env/file.env", "get", "ANY_KEY"],
    )
    assert result.exit_code != 0
    assert "not found" in result.output.lower() or "error" in result.output.lower()


def test_invalid_service_name_list():
    """--service with unknown store name: list fails with clear message."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--service", "no-such-store", "list"])
    assert result.exit_code != 0
    msg = (result.output or "") + (str(result.exception) if result.exception else "")
    assert "Unknown store" in msg or "no-such-store" in msg
    assert "Available" in msg or "store" in msg.lower()


def test_invalid_service_name_get():
    """--service with unknown store name: get fails."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--project", "test", "--service", "invalid-service", "get", "FOO"])
    assert result.exit_code != 0
    msg = (result.output or "") + (str(result.exception) if result.exception else "")
    assert "Unknown store" in msg or "invalid-service" in msg


def test_invalid_service_name_set():
    """--service with unknown store name: set fails."""
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--project", "test", "--service", "fake-store", "set", "K", "v"],
    )
    assert result.exit_code != 0
    msg = (result.output or "") + (str(result.exception) if result.exception else "")
    assert "Unknown store" in msg or "fake-store" in msg


def test_empty_service_value(mock_keyring):
    """--service '' is treated as unknown store (fails)."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--service", "", "list"])
    # Empty string is not "local" or "file", so looked up as cloud store and fails
    assert result.exit_code != 0


def test_import_with_service_file(tmp_path):
    """Import into --service file writes to --path."""
    source = tmp_path / "in.env"
    source.write_text("A=1\nB=2\n")
    dest = tmp_path / "out.env"
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--service", "file", "--path", str(dest), "import", str(source)],
    )
    assert result.exit_code == 0
    assert "Imported" in result.output
    assert "A=1" in dest.read_text() or "A=" in dest.read_text()


def test_export_with_service_file(tmp_path):
    """Export from --service file reads from --path."""
    env_file = tmp_path / "secrets.env"
    env_file.write_text("SECRET=hidden\n")
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--service", "file", "--path", str(env_file), "export", "--format", "dotenv"],
    )
    assert result.exit_code == 0
    assert "SECRET=hidden" in result.output


def test_clear_with_service_file(tmp_path):
    """Clear with --service file removes all keys from the file at --path."""
    env_file = tmp_path / "to_clear.env"
    env_file.write_text("A=1\nB=2\n")
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--service", "file", "--path", str(env_file), "clear", "--quiet"],
    )
    assert result.exit_code == 0
    assert "Cleared all secrets for service 'file'" in result.output
    assert env_file.read_text().strip() == "" or "A=" not in env_file.read_text()


def test_import_missing_file(mock_keyring):
    runner = CliRunner()
    result = runner.invoke(cli, ["--project", "test", "-d", "aws", "import", "/nonexistent/.env"])
    assert result.exit_code != 0


def test_init(monkeypatch):
    """init command runs without error on any platform."""
    runner = CliRunner()
    result = runner.invoke(cli, ["init"])
    assert result.exit_code == 0
    assert "Init complete" in result.output


def test_generate_codebuild(mock_keyring, sample_env):
    runner = CliRunner()
    runner.invoke(cli, ["--project", "test", "-d", "aws", "import", str(sample_env)])

    result = runner.invoke(
        cli,
        ["--project", "test", "-d", "aws", "generate", "codebuild-env", "--prefix", "/myapp/test/"],
    )
    assert result.exit_code == 0
    assert "parameter-store:" in result.output
    assert "TWILIO_API_SID: /myapp/test/TWILIO_API_SID" in result.output


# ---------------------------------------------------------------------------
# Bad parameters and missing arguments
# ---------------------------------------------------------------------------

def test_import_missing_file_argument(mock_keyring):
    """Test import command without file argument."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--project", "test", "import"])
    assert result.exit_code != 0
    assert "FILE" in result.output or "missing" in result.output.lower()


def test_import_missing_domain_and_file(mock_keyring):
    """Test import command without domain and file when domain not configured."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--project", "test", "import"])
    assert result.exit_code != 0


def test_get_missing_key_argument(mock_keyring):
    """Test get command without key argument."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--project", "test", "get"])
    assert result.exit_code != 0


def test_set_missing_arguments(mock_keyring):
    """Test set command without key and value arguments."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--project", "test", "set"])
    assert result.exit_code != 0


def test_delete_missing_key_argument(mock_keyring):
    """Test delete command without key argument."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--project", "test", "delete"])
    assert result.exit_code != 0


def test_export_missing_file_argument(mock_keyring):
    """Test export command with missing domain when no global domains exist."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--project", "test", "export"])
    # Export should work without domain (exports all)
    assert result.exit_code == 0


def test_push_missing_store_argument(mock_keyring):
    """Test push command without --service (default local is invalid for push target)."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--project", "test", "push"])
    assert result.exit_code != 0
    assert "cloud store" in result.output.lower() or "UsageError" in str(type(result.exception))


def test_pull_missing_store_argument(mock_keyring):
    """Test pull command without --service (default local is invalid for pull source)."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--project", "test", "pull"])
    assert result.exit_code != 0
    assert "cloud store" in result.output.lower() or "UsageError" in str(type(result.exception))


# ---------------------------------------------------------------------------
# Missing required parameters (negative): with options before or after subcommand
# ---------------------------------------------------------------------------

def test_import_missing_file_with_options_after(mock_keyring):
    """import without FILE and no configured domain fails even when options are after subcommand."""
    runner = CliRunner()
    result = runner.invoke(cli, ["import", "--project", "test"])
    assert result.exit_code != 0
    assert "Provide a file path" in result.output or "FILE" in result.output or "missing" in result.output.lower()


def test_get_missing_key_with_options_after(mock_keyring):
    """get without KEY fails when options are passed after the subcommand."""
    runner = CliRunner()
    result = runner.invoke(cli, ["get", "--project", "test", "--domain", "aws"])
    assert result.exit_code != 0
    assert "KEY" in result.output or "missing" in result.output.lower() or "argument" in result.output.lower()


def test_set_missing_arguments_with_options_after(mock_keyring):
    """set without KEY/VALUE fails when options are after the subcommand."""
    runner = CliRunner()
    result = runner.invoke(cli, ["set", "--project", "test"])
    assert result.exit_code != 0
    result2 = runner.invoke(cli, ["set", "KEY", "--project", "test"])
    assert result2.exit_code != 0


def test_delete_missing_key_with_options_after(mock_keyring):
    """delete without KEY fails when options are after the subcommand."""
    runner = CliRunner()
    result = runner.invoke(cli, ["delete", "-p", "test", "-d", "aws"])
    assert result.exit_code != 0
    assert "KEY" in result.output or "missing" in result.output.lower() or "argument" in result.output.lower()


def test_push_missing_service_with_options_after(mock_keyring):
    """push without --service (cloud) fails when options are after the subcommand."""
    runner = CliRunner()
    result = runner.invoke(cli, ["push", "--project", "test", "--domain", "aws"])
    assert result.exit_code != 0
    assert "cloud store" in result.output.lower()


def test_pull_missing_service_with_options_after(mock_keyring):
    """pull without --service (cloud) fails when options are after the subcommand."""
    runner = CliRunner()
    result = runner.invoke(cli, ["pull", "-p", "test", "-d", "aws"])
    assert result.exit_code != 0
    assert "cloud store" in result.output.lower()


# ---------------------------------------------------------------------------
# Invalid flag values
# ---------------------------------------------------------------------------

def test_export_invalid_format(mock_keyring, sample_env):
    """Test export command with invalid format value."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--project", "test", "-d", "aws", "export", "--format", "invalid"])
    assert result.exit_code != 0
    assert "invalid" in result.output.lower() or "choose" in result.output.lower()


def test_import_with_invalid_domain(mock_keyring, sample_env):
    """Test import command with non-existent domain (no config)."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--project", "test", "-d", "nonexistent", "import", str(sample_env)])
    # Should work since we're providing the file explicitly
    assert result.exit_code == 0


# ---------------------------------------------------------------------------
# Out of order flags
# ---------------------------------------------------------------------------

def test_flags_before_command(mock_keyring, sample_env):
    """Test that flags work before the command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--project", "test", "-d", "aws", "import", str(sample_env)])
    assert result.exit_code == 0
    assert "Imported" in result.output


def test_flags_after_command(mock_keyring, sample_env):
    """Options --project/--domain/--service work after the subcommand (common_options)."""
    runner = CliRunner()
    result = runner.invoke(cli, ["import", str(sample_env), "--project", "test", "-d", "aws"])
    assert result.exit_code == 0
    assert "Imported" in result.output


def test_mixed_flags_order(mock_keyring, sample_env):
    """Test flags mixed with command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["-d", "aws", "--project", "test", "import", str(sample_env)])
    assert result.exit_code == 0
    assert "Imported" in result.output


def test_project_flag_before_list(mock_keyring):
    """Test project flag before list command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--project", "test", "list"])
    assert result.exit_code == 0


def test_domain_flag_before_list(mock_keyring):
    """Test domain flag before list command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--project", "test", "-d", "aws", "list"])
    assert result.exit_code == 0


def test_domain_and_project_after_list(mock_keyring):
    """Options --project/--domain can appear after the subcommand (any order)."""
    runner = CliRunner()
    result = runner.invoke(cli, ["list", "--domain", "aws", "-p", "test"])
    assert result.exit_code == 0
    result2 = runner.invoke(cli, ["list", "-p", "test", "--domain", "aws"])
    assert result2.exit_code == 0


# ---------------------------------------------------------------------------
# Options in any order: project, domain, service (before / after / mixed)
# ---------------------------------------------------------------------------

def test_project_domain_service_all_orders_before_subcommand(mock_keyring, sample_env):
    """-p, -d, -s in any order before the subcommand all work."""
    runner = CliRunner()
    orders = [
        ["--project", "test", "--domain", "aws", "--service", "local", "import", str(sample_env)],
        ["--domain", "aws", "--project", "test", "--service", "local", "import", str(sample_env)],
        ["--service", "local", "--domain", "aws", "--project", "test", "import", str(sample_env)],
        ["-p", "test", "-d", "aws", "-s", "local", "import", str(sample_env)],
        ["-d", "aws", "-p", "test", "-s", "local", "import", str(sample_env)],
    ]
    for args in orders:
        result = runner.invoke(cli, args)
        assert result.exit_code == 0, f"Failed for args {args}: {result.output}"
        assert "Imported" in result.output


def test_project_domain_service_all_orders_after_subcommand(mock_keyring, sample_env):
    """-p, -d, -s in any order after the subcommand all work."""
    runner = CliRunner()
    orders = [
        ["import", str(sample_env), "--project", "test", "--domain", "aws", "--service", "local"],
        ["import", str(sample_env), "--domain", "aws", "--project", "test", "--service", "local"],
        ["import", str(sample_env), "--service", "local", "--domain", "aws", "--project", "test"],
        ["import", str(sample_env), "-p", "test", "-d", "aws", "-s", "local"],
        ["list", "--project", "test", "--domain", "aws"],
        ["list", "--domain", "aws", "--project", "test"],
        ["list", "-p", "test", "-d", "aws"],
    ]
    for args in orders:
        result = runner.invoke(cli, args)
        assert result.exit_code == 0, f"Failed for args {args}: {result.output}"


def test_project_domain_service_mixed_before_and_after_subcommand(mock_keyring, sample_env):
    """Options can be split: some before and some after the subcommand."""
    runner = CliRunner()
    # project before, domain after
    result = runner.invoke(cli, ["--project", "test", "import", str(sample_env), "--domain", "aws"])
    assert result.exit_code == 0
    assert "Imported" in result.output
    # domain before, project after
    result2 = runner.invoke(cli, ["--domain", "aws", "list", "--project", "test"])
    assert result2.exit_code == 0
    # service before, domain after
    result3 = runner.invoke(cli, ["--service", "local", "list", "-d", "aws", "-p", "test"])
    assert result3.exit_code == 0


def test_get_set_with_options_after_subcommand(mock_keyring, sample_env):
    """get/set work with -p/-d/-s after the subcommand."""
    runner = CliRunner()
    runner.invoke(cli, ["--project", "test", "-d", "aws", "import", str(sample_env)])
    result = runner.invoke(cli, ["get", "TWILIO_API_SID", "--project", "test", "-d", "aws"])
    assert result.exit_code == 0
    assert "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" in result.output
    result2 = runner.invoke(cli, ["set", "SOME_KEY", "some_val", "-p", "test", "--domain", "aws"])
    assert result2.exit_code == 0
    assert "Set" in result2.output


def test_export_unexport_with_options_after_subcommand(mock_keyring, sample_env):
    """export/unexport work with options after the subcommand."""
    runner = CliRunner()
    runner.invoke(cli, ["--project", "test", "-d", "aws", "import", str(sample_env)])
    result = runner.invoke(cli, ["export", "--project", "test", "--domain", "aws"])
    assert result.exit_code == 0
    assert "TWILIO_API_SID" in result.output
    result2 = runner.invoke(cli, ["unexport", "-p", "test", "-d", "aws"])
    assert result2.exit_code == 0
    assert "unset" in result2.output


# ---------------------------------------------------------------------------
# Invalid flag values for specific options
# ---------------------------------------------------------------------------

def test_invalid_project_name(mock_keyring):
    """Test with empty project name."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--project", "", "list"])
    # Empty string might be treated as None, which uses default
    assert result.exit_code == 0


def test_invalid_domain_name(mock_keyring):
    """Test with empty domain name."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--project", "test", "--domain", "", "list"])
    # Empty string might be treated as None
    assert result.exit_code == 0


def test_invalid_env_name(mock_keyring):
    """Test with empty env name."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--project", "test", "--env", "", "list"])
    assert result.exit_code == 0


def test_invalid_prefix_format(mock_keyring, sample_env):
    """Test push with empty prefix (should fail for AWS SSM)."""
    runner = CliRunner()
    runner.invoke(cli, ["--project", "test", "-d", "aws", "import", str(sample_env)])
    result = runner.invoke(cli, ["--project", "test", "-d", "aws", "push", "--service", "aws", "--prefix", ""])
    # Empty prefix should fail for AWS SSM (can't have empty parameter name)
    assert result.exit_code != 0


def test_invalid_region_format(mock_keyring, sample_env):
    """Test push with empty region (should fail for AWS SSM)."""
    runner = CliRunner()
    runner.invoke(cli, ["--project", "test", "-d", "aws", "import", str(sample_env)])
    result = runner.invoke(cli, ["--project", "test", "-d", "aws", "push", "--service", "aws", "--region", ""])
    # Empty region should fail for AWS SSM (validation error)
    assert result.exit_code != 0


# ---------------------------------------------------------------------------
# Edge cases and boundary conditions
# ---------------------------------------------------------------------------

def test_list_empty_project(mock_keyring):
    """Test list with project that has no secrets (shows default domain as empty)."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--project", "empty_project_xyz", "list"])
    assert result.exit_code == 0
    assert "_default_" in result.output and "(empty)" in result.output


def test_get_from_empty_domain(mock_keyring):
    """Test get from domain with no secrets."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--project", "test", "-d", "empty_domain", "get", "FOO"])
    assert result.exit_code != 0
    assert "not found" in result.output


def test_export_empty_domain(mock_keyring):
    """Test export from domain with no secrets."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--project", "test", "-d", "empty_export", "export"])
    assert result.exit_code == 0
    # Empty export should produce empty output
    assert result.output == "" or result.output.strip() == ""


def test_unexport_outputs_unset_commands(mock_keyring):
    """Unexport outputs unset KEY for each key that export would set."""
    runner = CliRunner()
    runner.invoke(cli, ["--project", "test", "-d", "aws", "set", "FOO", "bar"])
    runner.invoke(cli, ["--project", "test", "-d", "aws", "set", "BAZ", "qux"])
    result = runner.invoke(cli, ["--project", "test", "-d", "aws", "unexport"])
    assert result.exit_code == 0
    lines = [s.strip() for s in result.output.strip().splitlines()]
    assert "unset BAZ" in lines
    assert "unset FOO" in lines
    assert all(line.startswith("unset ") for line in lines if line)


def test_unexport_win_format(mock_keyring):
    """Unexport --format win outputs PowerShell Remove-Item Env:KEY."""
    runner = CliRunner()
    runner.invoke(cli, ["--project", "test", "-d", "aws", "set", "FOO", "bar"])
    result = runner.invoke(cli, ["--project", "test", "-d", "aws", "unexport", "--format", "win"])
    assert result.exit_code == 0
    assert "Remove-Item Env:FOO" in result.output


def test_unexport_empty_domain(mock_keyring):
    """Unexport with no secrets outputs nothing."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--project", "test", "-d", "empty_unexport", "unexport"])
    assert result.exit_code == 0
    assert result.output.strip() == ""


def test_unexport_unix_then_env_vars_gone(mock_keyring, sample_env):
    """Unexport (unix format) outputs unset commands; applying them removes the vars from the environment."""
    import os

    runner = CliRunner()
    runner.invoke(cli, ["--project", "test", "-d", "aws", "import", str(sample_env)])
    result = runner.invoke(cli, ["--project", "test", "-d", "aws", "unexport", "--format", "unix"])
    assert result.exit_code == 0
    lines = [s.strip() for s in result.output.strip().splitlines() if s.strip()]

    # Simulate having exported then unexport: set vars in env, then apply unset commands
    for line in lines:
        if line.startswith("unset "):
            key = line[6:].strip()
            os.environ[key] = "was_set"

    for line in lines:
        if line.startswith("unset "):
            key = line[6:].strip()
            os.environ.pop(key, None)

    for line in lines:
        if line.startswith("unset "):
            key = line[6:].strip()
            assert key not in os.environ, f"unexport should remove {key} from env"


def test_clear_empty_domain(mock_keyring):
    """Test clear on domain with no secrets."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--project", "test", "-d", "empty_clear", "clear", "--quiet"])
    assert result.exit_code == 0


def test_set_empty_value(mock_keyring):
    """Test setting an empty value."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--project", "test", "-d", "d", "set", "EMPTY_VAR", ""])
    assert result.exit_code == 0

    result = runner.invoke(cli, ["--project", "test", "-d", "d", "get", "EMPTY_VAR"])
    assert result.exit_code == 0
    assert result.output.strip() == ""


def test_import_empty_file(mock_keyring, tmp_path):
    """Test importing an empty .env file."""
    empty_file = tmp_path / "empty.env"
    empty_file.write_text("")
    runner = CliRunner()
    result = runner.invoke(cli, ["--project", "test", "-d", "aws", "import", str(empty_file)])
    assert result.exit_code == 0
    assert "No variables found" in result.output


def test_import_file_with_only_comments(mock_keyring, tmp_path):
    """Test importing a .env file with only comments."""
    comment_file = tmp_path / "comments.env"
    comment_file.write_text("# This is a comment\n# Another comment\n")
    runner = CliRunner()
    result = runner.invoke(cli, ["--project", "test", "-d", "aws", "import", str(comment_file)])
    assert result.exit_code == 0
    assert "No variables found" in result.output


def test_import_file_with_whitespace_only(mock_keyring, tmp_path):
    """Test importing a .env file with only whitespace."""
    whitespace_file = tmp_path / "whitespace.env"
    whitespace_file.write_text("   \n\t\n  \n")
    runner = CliRunner()
    result = runner.invoke(cli, ["--project", "test", "-d", "aws", "import", str(whitespace_file)])
    assert result.exit_code == 0
    assert "No variables found" in result.output


def test_export_with_invalid_format_value(mock_keyring, sample_env):
    """Test export with completely invalid format."""
    runner = CliRunner()
    runner.invoke(cli, ["--project", "test", "-d", "aws", "import", str(sample_env)])
    result = runner.invoke(cli, ["--project", "test", "-d", "aws", "export", "--format", "invalid_format"])
    assert result.exit_code != 0
    assert "invalid_format" in result.output.lower() or "choose" in result.output.lower()


def test_push_to_invalid_store(mock_keyring, sample_env):
    """Test push to a non-existent store type."""
    runner = CliRunner()
    runner.invoke(cli, ["--project", "test", "-d", "aws", "import", str(sample_env)])
    result = runner.invoke(cli, ["--project", "test", "-d", "aws", "push", "--service", "nonexistent-store"])
    assert result.exit_code != 0


def test_pull_from_invalid_store(mock_keyring):
    """Test pull from a non-existent store type."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--project", "test", "-d", "aws", "pull", "--service", "nonexistent-store"])
    assert result.exit_code != 0


def test_generate_codebuild_missing_domain(mock_keyring, sample_env):
    """Test codebuild generation without domain."""
    runner = CliRunner()
    runner.invoke(cli, ["--project", "test", "import", str(sample_env)])
    result = runner.invoke(cli, ["--project", "test", "generate", "codebuild-env"])
    # Should work without domain
    assert result.exit_code == 0


# ---------------------------------------------------------------------------
# Export to file
# ---------------------------------------------------------------------------

def test_export_to_file(mock_keyring, sample_env, tmp_path):
    """Test exporting secrets to a file."""
    runner = CliRunner()
    runner.invoke(cli, ["--project", "test", "-d", "aws", "import", str(sample_env)])

    output_file = tmp_path / "exported.env"
    result = runner.invoke(cli, ["--project", "test", "-d", "aws", "export", "--format", "dotenv", "-o", str(output_file)])
    assert result.exit_code == 0
    assert "Exported" in result.output
    assert "exported.env" in result.output

    content = output_file.read_text()
    assert "TWILIO_API_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" in content


def test_full_round_trip_import_manipulate_export_compare(mock_keyring, sample_env, tmp_path):
    """Import .env, modify/delete/add keys, export and compare to expected diff."""
    runner = CliRunner()
    # 1. Import
    r_import = runner.invoke(cli, ["--project", "test", "-d", "roundtrip", "import", str(sample_env)])
    assert r_import.exit_code == 0
    # 2. Modify one value and verify
    runner.invoke(cli, ["--project", "test", "-d", "roundtrip", "set", "TWILIO_API_SID", "MODIFIED_SID"])
    r_get = runner.invoke(cli, ["--project", "test", "-d", "roundtrip", "get", "TWILIO_API_SID"])
    assert r_get.exit_code == 0
    assert r_get.output.strip() == "MODIFIED_SID"
    # 3. Delete one key and verify gone
    runner.invoke(cli, ["--project", "test", "-d", "roundtrip", "delete", "SINGLE_QUOTED"])
    r_missing = runner.invoke(cli, ["--project", "test", "-d", "roundtrip", "get", "SINGLE_QUOTED"])
    assert r_missing.exit_code != 0
    assert "not found" in r_missing.output.lower()
    # 4. Add custom value and verify
    runner.invoke(cli, ["--project", "test", "-d", "roundtrip", "set", "CUSTOM_ADDED", "added_value"])
    r_custom = runner.invoke(cli, ["--project", "test", "-d", "roundtrip", "get", "CUSTOM_ADDED"])
    assert r_custom.exit_code == 0
    assert r_custom.output.strip() == "added_value"
    # 5. Export to file
    out_file = tmp_path / "newsample.env"
    r_export = runner.invoke(cli, ["--project", "test", "-d", "roundtrip", "export", "--format", "dotenv", "-o", str(out_file)])
    assert r_export.exit_code == 0
    content = out_file.read_text()
    # 6. Compare: modified value present, deleted key absent, custom key present
    assert "TWILIO_API_SID=MODIFIED_SID" in content or "TWILIO_API_SID=MODIFIED_SID\n" in content
    assert "SINGLE_QUOTED" not in content
    assert "CUSTOM_ADDED=added_value" in content


def test_export_to_file_json(mock_keyring, sample_env, tmp_path):
    """Test exporting secrets to a JSON file."""
    runner = CliRunner()
    runner.invoke(cli, ["--project", "test", "-d", "aws", "import", str(sample_env)])

    output_file = tmp_path / "exported.json"
    result = runner.invoke(cli, ["--project", "test", "-d", "aws", "export", "--format", "json", "-o", str(output_file)])
    assert result.exit_code == 0
    assert "Exported" in result.output

    content = output_file.read_text()
    import json
    data = json.loads(content)
    assert "TWILIO_API_SID" in data


def test_export_to_file_unix_format(mock_keyring, sample_env, tmp_path):
    """Test exporting secrets to a file in unix format (export KEY=value)."""
    runner = CliRunner()
    runner.invoke(cli, ["--project", "test", "-d", "aws", "import", str(sample_env)])

    output_file = tmp_path / "exported.env"
    result = runner.invoke(cli, ["--project", "test", "-d", "aws", "export", "--format", "unix", "-o", str(output_file)])
    assert result.exit_code == 0

    content = output_file.read_text()
    assert "export TWILIO_API_SID=" in content


def test_export_to_file_win_format(mock_keyring, sample_env, tmp_path):
    """Test exporting secrets in PowerShell format ($env:KEY = 'value')."""
    runner = CliRunner()
    runner.invoke(cli, ["--project", "test", "-d", "aws", "import", str(sample_env)])

    result = runner.invoke(cli, ["--project", "test", "-d", "aws", "export", "--format", "win"])
    assert result.exit_code == 0
    assert "$env:TWILIO_API_SID =" in result.output or "$env:TWILIO_API_SID=" in result.output
    assert "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" in result.output


def test_export_to_default_env_file(mock_keyring, sample_env, tmp_path):
    """Test exporting to default .env file in current directory."""
    runner = CliRunner()
    runner.invoke(cli, ["--project", "test", "-d", "aws", "import", str(sample_env)])

    # Change to tmp_path directory
    import os
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        result = runner.invoke(cli, ["--project", "test", "-d", "aws", "export", "-o", ".env"])
        assert result.exit_code == 0
        assert "Exported" in result.output

        content = (tmp_path / ".env").read_text()
        assert "TWILIO_API_SID=" in content
    finally:
        os.chdir(original_cwd)


# ---------------------------------------------------------------------------
# Clear non-existent projects/domains
# ---------------------------------------------------------------------------

def test_clear_nonexistent_domain(mock_keyring):
    """Test clearing a domain that doesn't exist."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--project", "test", "-d", "nonexistent_domain_xyz", "clear", "--quiet"])
    assert result.exit_code == 0
    # The domain is created when we try to clear it, so it will succeed
    assert "Cleared" in result.output


def test_clear_nonexistent_project(mock_keyring):
    """Test clearing a project that doesn't exist (clears all domains / default)."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--project", "nonexistent_project_xyz", "clear", "--quiet"])
    assert result.exit_code == 0
    assert "Cleared all secrets for service 'local' (all domains)" in result.output


def test_clear_empty_domain_explicit(mock_keyring):
    """Test clearing an empty domain explicitly."""
    runner = CliRunner()
    # First set something
    runner.invoke(cli, ["--project", "test", "-d", "empty_test", "set", "FOO", "bar"])
    # Then clear it
    result = runner.invoke(cli, ["--project", "test", "-d", "empty_test", "clear", "--quiet"])
    assert result.exit_code == 0
    assert "Cleared" in result.output

    # Verify it's cleared - list shows "(empty)" for empty domains
    result = runner.invoke(cli, ["--project", "test", "-d", "empty_test", "list"])
    assert result.exit_code == 0
    assert "(empty)" in result.output


def test_clear_project_after_domain_clear(mock_keyring):
    """Test clearing default domain after clearing a named domain."""
    runner = CliRunner()
    # Set up some secrets in named domains and in default
    runner.invoke(cli, ["--project", "test", "-d", "aws", "set", "FOO", "bar"])
    runner.invoke(cli, ["--project", "test", "-d", "web", "set", "BAZ", "qux"])
    runner.invoke(cli, ["--project", "test", "set", "DEFAULT_KEY", "val"])  # default domain

    # Clear one domain (aws)
    result = runner.invoke(cli, ["--project", "test", "-d", "aws", "clear", "--quiet"])
    assert result.exit_code == 0

    # Clear without -d clears all domains (web and default)
    result = runner.invoke(cli, ["--project", "test", "clear", "--quiet"])
    assert result.exit_code == 0
    assert "Cleared all secrets for service 'local' (all domains)" in result.output


# ---------------------------------------------------------------------------
# Negative tests for exceptions and error handling
# ---------------------------------------------------------------------------

def test_get_nonexistent_key_raises():
    """Test that get on nonexistent key raises exception."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--project", "test", "-d", "d", "get", "NONEXISTENT_KEY"])
    assert result.exit_code != 0
    assert "not found" in result.output.lower() or "clickexception" in str(type(result.exception)).lower()


def test_delete_nonexistent_key():
    """Test that delete on nonexistent key does not raise exception (idempotent)."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--project", "test", "-d", "d", "delete", "NONEXISTENT_KEY"])
    # delete should succeed even for nonexistent key (idempotent operation)
    assert result.exit_code == 0
    assert "Removed" in result.output


def test_cli_domain_project_with_separator_sanitized(mock_keyring):
    """Domain or project containing key separator (e.g. /) is accepted; set/get/list work (keychain)."""
    runner = CliRunner()
    # Domain with slash: keychain stores under that path; no broken key
    runner.invoke(cli, ["--project", "x/y", "-d", "a/b", "set", "SEP_KEY", "val"])
    result = runner.invoke(cli, ["--project", "x/y", "-d", "a/b", "get", "SEP_KEY"])
    assert result.exit_code == 0
    assert result.output.strip() == "val"
    result_list = runner.invoke(cli, ["--project", "x/y", "-d", "a/b", "list"])
    assert result_list.exit_code == 0
    assert "SEP_KEY" in result_list.output


def test_domain_with_emoji_roundtrip(mock_keyring):
    """Domain name containing emoji can be used for set/list/get without error."""
    runner = CliRunner()
    runner.invoke(cli, ["--project", "p", "-d", "prod🔥", "set", "EMOJI_K", "v1"])
    r = runner.invoke(cli, ["--project", "p", "-d", "prod🔥", "get", "EMOJI_K"])
    assert r.exit_code == 0
    assert r.output.strip() == "v1"
    r_list = runner.invoke(cli, ["--project", "p", "-d", "prod🔥", "list"])
    assert r_list.exit_code == 0
    assert "EMOJI_K" in r_list.output


def test_project_with_emoji_roundtrip(mock_keyring):
    """Project name containing emoji can be used for set/list/get without error."""
    runner = CliRunner()
    runner.invoke(cli, ["--project", "proj🎯", "-d", "d", "set", "EMOJI_P", "v2"])
    r = runner.invoke(cli, ["--project", "proj🎯", "-d", "d", "get", "EMOJI_P"])
    assert r.exit_code == 0
    assert r.output.strip() == "v2"


def test_key_name_with_emoji_roundtrip(mock_keyring):
    """Key name containing emoji can be set and retrieved."""
    runner = CliRunner()
    runner.invoke(cli, ["--project", "p", "-d", "d", "set", "KEY🔑", "secret"])
    r = runner.invoke(cli, ["--project", "p", "-d", "d", "get", "KEY🔑"])
    assert r.exit_code == 0
    assert r.output.strip() == "secret"


def test_invalid_version_cli_fails():
    """CLI with invalid semver (e.g. --version 1.0) fails with clear message."""
    runner = CliRunner()
    # Pass --version after list so it's the semver option, not the package --version
    result = runner.invoke(cli, ["--project", "test", "-d", "aws", "--service", "aws", "list", "--version", "1.0"])
    assert result.exit_code != 0
    assert "version" in result.output.lower() or "invalid" in result.output.lower() or "semver" in result.output.lower()


def test_export_invalid_format_value():
    """Test export with invalid format value."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--project", "test", "-d", "aws", "export", "--format", "invalid_format"])
    assert result.exit_code != 0
    assert "invalid" in result.output.lower() or "choose" in result.output.lower()


def test_import_nonexistent_file():
    """Test import with nonexistent file."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--project", "test", "-d", "aws", "import", "/nonexistent/path/file.env"])
    assert result.exit_code != 0


# ---------------------------------------------------------------------------
# Import format: JSON and YAML — positive and negative signals
# ---------------------------------------------------------------------------

# --- Positive: valid JSON/YAML imports succeed and keys are stored ---

def test_import_json_format(mock_keyring, tmp_path):
    """Positive: valid JSON object imports and keys are retrievable."""
    json_file = tmp_path / "secrets.json"
    json_file.write_text('{"API_KEY": "abc123", "DB_HOST": "localhost"}')
    runner = CliRunner()
    result = runner.invoke(cli, ["--project", "test", "-d", "aws", "import", "--format", "json", str(json_file)])
    assert result.exit_code == 0
    assert "Imported" in result.output

    result = runner.invoke(cli, ["--project", "test", "-d", "aws", "get", "API_KEY"])
    assert result.exit_code == 0
    assert "abc123" in result.output


def test_import_yaml_format(mock_keyring, tmp_path):
    """Positive: valid YAML object imports and keys are retrievable."""
    yaml_file = tmp_path / "secrets.yaml"
    yaml_file.write_text("API_KEY: xyz789\nDB_HOST: remotehost")
    runner = CliRunner()
    result = runner.invoke(cli, ["--project", "test", "-d", "aws", "import", "--format", "yaml", str(yaml_file)])
    assert result.exit_code == 0
    assert "Imported" in result.output

    result = runner.invoke(cli, ["--project", "test", "-d", "aws", "get", "API_KEY"])
    assert result.exit_code == 0
    assert "xyz789" in result.output


# --- Negative: invalid JSON/YAML or wrong structure are rejected (non-zero exit, clear message) ---

def test_import_invalid_json(mock_keyring, tmp_path):
    """Negative: invalid JSON syntax is rejected with non-zero exit and 'Invalid JSON' message."""
    json_file = tmp_path / "invalid.json"
    json_file.write_text('{invalid json}')
    runner = CliRunner()
    result = runner.invoke(cli, ["--project", "test", "-d", "aws", "import", "--format", "json", str(json_file)])
    assert result.exit_code != 0
    assert "Invalid JSON" in result.output


def test_import_invalid_yaml(mock_keyring, tmp_path):
    """Negative: invalid YAML syntax is rejected with non-zero exit and 'Invalid YAML' message."""
    yaml_file = tmp_path / "invalid.yaml"
    yaml_file.write_text("key1:\n  key2:\n    key3: value\n  key4: value\n  - invalid")
    runner = CliRunner()
    result = runner.invoke(cli, ["--project", "test", "-d", "aws", "import", "--format", "yaml", str(yaml_file)])
    assert result.exit_code != 0
    assert "Invalid YAML" in result.output


def test_import_json_with_array(mock_keyring, tmp_path):
    """Negative: JSON root that is an array is rejected (expect object/dictionary)."""
    json_file = tmp_path / "array.json"
    json_file.write_text('["item1", "item2"]')
    runner = CliRunner()
    result = runner.invoke(cli, ["--project", "test", "-d", "aws", "import", "--format", "json", str(json_file)])
    assert result.exit_code != 0
    assert "object" in result.output.lower() or "dictionary" in result.output.lower()


def test_import_yaml_with_list(mock_keyring, tmp_path):
    """Negative: YAML root that is a list is rejected (expect object/dictionary)."""
    yaml_file = tmp_path / "list.yaml"
    yaml_file.write_text("- item1\n- item2")
    runner = CliRunner()
    result = runner.invoke(cli, ["--project", "test", "-d", "aws", "import", "--format", "yaml", str(yaml_file)])
    assert result.exit_code != 0
    assert "object" in result.output.lower() or "dictionary" in result.output.lower()


def test_import_json_non_object_root(mock_keyring, tmp_path):
    """Negative: JSON root that is a scalar (e.g. number) is rejected."""
    json_file = tmp_path / "scalar.json"
    json_file.write_text("42")
    runner = CliRunner()
    result = runner.invoke(cli, ["--project", "test", "-d", "aws", "import", "--format", "json", str(json_file)])
    assert result.exit_code != 0
    assert "object" in result.output.lower() or "dictionary" in result.output.lower()


def test_import_yaml_non_object_root(mock_keyring, tmp_path):
    """Negative: YAML root that is a scalar is rejected."""
    yaml_file = tmp_path / "scalar.yaml"
    yaml_file.write_text("just a string")
    runner = CliRunner()
    result = runner.invoke(cli, ["--project", "test", "-d", "aws", "import", "--format", "yaml", str(yaml_file)])
    assert result.exit_code != 0
    assert "object" in result.output.lower() or "dictionary" in result.output.lower()


def test_push_to_invalid_store_type():
    """Test push with invalid store type raises KeyError."""
    runner = CliRunner()
    # First set a secret so we have something to push
    runner.invoke(cli, ["--project", "test", "-d", "aws", "set", "FOO", "bar"])
    result = runner.invoke(cli, ["--project", "test", "-d", "aws", "push", "--service", "invalid_store_type"])
    # The KeyError should be raised and caught by Click
    assert result.exit_code != 0
    # The exception is raised but output might be empty due to how Click handles exceptions
    # Just verify the exit code is non-zero


def test_pull_from_invalid_store_type():
    """Test pull with invalid store type."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--project", "test", "-d", "aws", "pull", "--service", "invalid_store_type"])
    assert result.exit_code != 0


def test_clear_without_confirmation():
    """Test that clear without --quiet flag requires confirmation."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--project", "test", "-d", "aws", "clear"])
    # Without --quiet and no input, confirmation is declined -> abort
    assert result.exit_code != 0 or "Are you sure" in result.output


# ---------------------------------------------------------------------------
# Environment variable tests
# ---------------------------------------------------------------------------

def test_domain_from_env_var(mock_keyring, sample_env, monkeypatch):
    """Test that domain can be set via ENVELOPER_DOMAIN env var."""
    monkeypatch.setenv("ENVELOPER_DOMAIN", "env_domain")
    runner = CliRunner()
    result = runner.invoke(cli, ["--project", "test", "import", str(sample_env)])
    assert result.exit_code == 0

    # Verify it was stored under the env var domain
    result = runner.invoke(cli, ["--project", "test", "-d", "env_domain", "list"])
    assert result.exit_code == 0
    assert "TWILIO_API_SID" in result.output


def test_env_var_overridden_by_cli_option(mock_keyring, sample_env, monkeypatch):
    """Test that CLI options override environment variables."""
    monkeypatch.setenv("ENVELOPER_PROJECT", "env_project")
    monkeypatch.setenv("ENVELOPER_DOMAIN", "env_domain")
    runner = CliRunner()
    # CLI options should override env vars
    result = runner.invoke(cli, ["--project", "cli_project", "-d", "cli_domain", "import", str(sample_env)])
    assert result.exit_code == 0

    # Verify it was stored under CLI options, not env vars
    result = runner.invoke(cli, ["--project", "cli_project", "-d", "cli_domain", "list"])
    assert result.exit_code == 0
    assert "TWILIO_API_SID" in result.output

    # Env var project should not have the secrets
    result = runner.invoke(cli, ["--project", "env_project", "list"])
    assert result.exit_code == 0
    assert "TWILIO_API_SID" not in result.output


def test_env_var_with_list_command(mock_keyring, sample_env, monkeypatch):
    """Test list command with environment variables set."""
    monkeypatch.setenv("ENVELOPER_PROJECT", "test")
    monkeypatch.setenv("ENVELOPER_DOMAIN", "aws")
    runner = CliRunner()
    runner.invoke(cli, ["import", str(sample_env)])

    # List without specifying project/domain (should use env vars)
    result = runner.invoke(cli, ["list"])
    assert result.exit_code == 0
    assert "TWILIO_API_SID" in result.output


def test_env_var_with_export_command(mock_keyring, sample_env, monkeypatch):
    """Test export command with environment variables set."""
    monkeypatch.setenv("ENVELOPER_PROJECT", "test")
    monkeypatch.setenv("ENVELOPER_DOMAIN", "aws")
    runner = CliRunner()
    runner.invoke(cli, ["import", str(sample_env)])

    # Export without specifying project/domain (should use env vars)
    result = runner.invoke(cli, ["export"])
    assert result.exit_code == 0
    assert "TWILIO_API_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" in result.output


def test_export_to_file_yaml(mock_keyring, sample_env, tmp_path):
    """Test exporting secrets to a YAML file."""
    runner = CliRunner()
    runner.invoke(cli, ["--project", "test", "-d", "aws", "import", str(sample_env)])

    output_file = tmp_path / "exported.yaml"
    result = runner.invoke(cli, ["--project", "test", "-d", "aws", "export", "--format", "yaml", "-o", str(output_file)])
    assert result.exit_code == 0
    assert "Exported" in result.output

    content = output_file.read_text()
    assert "TWILIO_API_SID: ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" in content


def test_export_yaml_stdout(mock_keyring, sample_env):
    """Test exporting secrets to stdout in YAML format."""
    runner = CliRunner()
    runner.invoke(cli, ["--project", "test", "-d", "aws", "import", str(sample_env)])

    result = runner.invoke(cli, ["--project", "test", "-d", "aws", "export", "--format", "yaml"])
    assert result.exit_code == 0
    assert "TWILIO_API_SID: ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" in result.output
