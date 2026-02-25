"""Tests for CLI commands via click.testing.CliRunner."""

from __future__ import annotations

from click.testing import CliRunner

from enveloper.cli import cli


def test_version():
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


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
    result = runner.invoke(cli, ["--project", "test", "-d", "d", "rm", "FOO"])
    assert result.exit_code == 0

    result = runner.invoke(cli, ["--project", "test", "-d", "d", "get", "FOO"])
    assert result.exit_code != 0


def test_clear(mock_keyring):
    runner = CliRunner()
    runner.invoke(cli, ["--project", "test", "-d", "d", "set", "A", "1"])
    runner.invoke(cli, ["--project", "test", "-d", "d", "set", "B", "2"])
    result = runner.invoke(cli, ["--project", "test", "-d", "d", "clear", "--yes"])
    assert result.exit_code == 0
    assert "Cleared" in result.output


def test_stores():
    runner = CliRunner()
    result = runner.invoke(cli, ["stores"])
    assert result.exit_code == 0
    assert "keychain" in result.output
    assert "aws-ssm" in result.output
    assert "github" in result.output


def test_import_missing_file(mock_keyring):
    runner = CliRunner()
    result = runner.invoke(cli, ["--project", "test", "-d", "aws", "import", "/nonexistent/.env"])
    assert result.exit_code != 0


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
