"""Tests for the python-dotenv-style SDK (load_dotenv, dotenv_values)."""

from __future__ import annotations

import os

from enveloper import dotenv_values, load_dotenv


def test_load_dotenv_import():
    """from enveloper import load_dotenv works."""
    from enveloper import load_dotenv as ld

    assert callable(ld)


def test_load_dotenv_loads_from_keychain(mock_keyring, sample_env):
    """load_dotenv(project, domain) loads keychain secrets into os.environ."""
    from click.testing import CliRunner

    from enveloper.cli import cli

    runner = CliRunner()
    runner.invoke(cli, ["--project", "test", "-d", "aws", "import", str(sample_env)])

    # Clear any existing so we can assert they were set by load_dotenv
    for key in ("TWILIO_API_SID", "TWILIO_AUTH_TOKEN", "AWS_PROFILE"):
        os.environ.pop(key, None)

    try:
        result = load_dotenv(project="test", domain="aws")
        assert result is True
        assert os.environ.get("TWILIO_API_SID") == "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        assert os.environ.get("TWILIO_AUTH_TOKEN") == "my secret token"
        assert os.environ.get("AWS_PROFILE") == "default"
    finally:
        for key in ("TWILIO_API_SID", "TWILIO_AUTH_TOKEN", "AWS_PROFILE"):
            os.environ.pop(key, None)


def test_load_dotenv_override_false(mock_keyring, sample_env):
    """load_dotenv(override=False) does not overwrite existing os.environ."""
    from click.testing import CliRunner

    from enveloper.cli import cli

    runner = CliRunner()
    runner.invoke(cli, ["--project", "test", "-d", "aws", "import", str(sample_env)])

    os.environ["TWILIO_API_SID"] = "already_set"
    try:
        result = load_dotenv(project="test", domain="aws", override=False)
        assert result is True  # we did set some other vars
        assert os.environ["TWILIO_API_SID"] == "already_set"
    finally:
        os.environ.pop("TWILIO_API_SID", None)
        for key in ("TWILIO_AUTH_TOKEN", "AWS_PROFILE"):
            os.environ.pop(key, None)


def test_load_dotenv_override_true(mock_keyring, sample_env):
    """load_dotenv(override=True) overwrites existing os.environ."""
    from click.testing import CliRunner

    from enveloper.cli import cli

    runner = CliRunner()
    runner.invoke(cli, ["--project", "test", "-d", "aws", "import", str(sample_env)])

    os.environ["TWILIO_API_SID"] = "old_value"
    try:
        result = load_dotenv(project="test", domain="aws", override=True)
        assert result is True
        assert os.environ["TWILIO_API_SID"] == "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    finally:
        for key in ("TWILIO_API_SID", "TWILIO_AUTH_TOKEN", "AWS_PROFILE"):
            os.environ.pop(key, None)


def test_load_dotenv_empty_returns_false(mock_keyring):
    """load_dotenv when keychain has no secrets returns False."""
    result = load_dotenv(project="empty_project_xyz", domain="empty_domain")
    assert result is False


def test_dotenv_values_returns_dict(mock_keyring, sample_env):
    """dotenv_values(project, domain) returns dict without modifying os.environ."""
    from click.testing import CliRunner

    from enveloper.cli import cli

    runner = CliRunner()
    runner.invoke(cli, ["--project", "test", "-d", "aws", "import", str(sample_env)])

    before = os.environ.get("TWILIO_API_SID")
    data = dotenv_values(project="test", domain="aws")
    after = os.environ.get("TWILIO_API_SID")
    assert before == after  # unchanged
    assert isinstance(data, dict)
    assert data.get("TWILIO_API_SID") == "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    assert data.get("AWS_PROFILE") == "default"


def test_dotenv_values_empty(mock_keyring):
    """dotenv_values for empty keychain returns empty dict."""
    data = dotenv_values(project="empty_xyz", domain="empty")
    assert data == {}


def test_load_dotenv_resolves_from_env(mock_keyring, sample_env, monkeypatch):
    """load_dotenv uses ENVELOPER_PROJECT and ENVELOPER_DOMAIN when project/domain not passed."""
    from click.testing import CliRunner

    from enveloper.cli import cli

    runner = CliRunner()
    runner.invoke(cli, ["--project", "sdk_project", "-d", "sdk_domain", "import", str(sample_env)])

    monkeypatch.setenv("ENVELOPER_PROJECT", "sdk_project")
    monkeypatch.setenv("ENVELOPER_DOMAIN", "sdk_domain")
    for key in ("TWILIO_API_SID", "TWILIO_AUTH_TOKEN", "AWS_PROFILE"):
        os.environ.pop(key, None)
    try:
        result = load_dotenv()  # no project/domain
        assert result is True
        assert os.environ.get("TWILIO_API_SID") == "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    finally:
        for key in ("TWILIO_API_SID", "TWILIO_AUTH_TOKEN", "AWS_PROFILE"):
            os.environ.pop(key, None)


def test_load_dotenv_default_domain_when_unspecified(mock_keyring, sample_env, monkeypatch):
    """When domain is not passed and ENVELOPER_DOMAIN is unset, domain defaults to 'default'."""
    from click.testing import CliRunner

    from enveloper.cli import cli

    runner = CliRunner()
    runner.invoke(cli, ["--project", "test", "import", str(sample_env)])  # no -d -> domain "default"
    monkeypatch.delenv("ENVELOPER_DOMAIN", raising=False)
    monkeypatch.delenv("ENVELOPER_PROJECT", raising=False)
    for key in ("TWILIO_API_SID", "TWILIO_AUTH_TOKEN", "AWS_PROFILE"):
        os.environ.pop(key, None)
    try:
        result = load_dotenv(project="test")  # domain not passed
        assert result is True
        assert os.environ.get("TWILIO_API_SID") == "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    finally:
        for key in ("TWILIO_API_SID", "TWILIO_AUTH_TOKEN", "AWS_PROFILE"):
            os.environ.pop(key, None)


# ---------------------------------------------------------------------------
# service and path parameters
# ---------------------------------------------------------------------------

def test_load_dotenv_service_local_explicit(mock_keyring, sample_env):
    """load_dotenv(service="local") behaves like default (keychain)."""
    from click.testing import CliRunner

    from enveloper.cli import cli

    runner = CliRunner()
    runner.invoke(cli, ["--project", "test", "-d", "aws", "import", str(sample_env)])
    for key in ("TWILIO_API_SID", "TWILIO_AUTH_TOKEN", "AWS_PROFILE"):
        os.environ.pop(key, None)
    try:
        result = load_dotenv(project="test", domain="aws", service="local")
        assert result is True
        assert os.environ.get("TWILIO_API_SID") == "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    finally:
        for key in ("TWILIO_API_SID", "TWILIO_AUTH_TOKEN", "AWS_PROFILE"):
            os.environ.pop(key, None)


def test_load_dotenv_service_file(tmp_path):
    """load_dotenv(service="file", path=...) loads from .env file."""
    env_file = tmp_path / "sdk.env"
    env_file.write_text("SDK_FOO=from_file\nSDK_BAR=123\n")
    os.environ.pop("SDK_FOO", None)
    os.environ.pop("SDK_BAR", None)
    try:
        result = load_dotenv(service="file", path=str(env_file))
        assert result is True
        assert os.environ.get("SDK_FOO") == "from_file"
        assert os.environ.get("SDK_BAR") == "123"
    finally:
        os.environ.pop("SDK_FOO", None)
        os.environ.pop("SDK_BAR", None)


def test_dotenv_values_service_file(tmp_path):
    """dotenv_values(service="file", path=...) returns dict from file without touching os.environ."""
    env_file = tmp_path / "values.env"
    env_file.write_text("X=1\nY=2\n")
    before_x = os.environ.get("X")
    data = dotenv_values(service="file", path=str(env_file))
    after_x = os.environ.get("X")
    assert before_x == after_x
    assert data == {"X": "1", "Y": "2"}


def test_dotenv_values_service_file_empty(tmp_path):
    """dotenv_values(service="file", path=...) with empty file returns empty dict."""
    empty_file = tmp_path / "empty.env"
    empty_file.write_text("")
    data = dotenv_values(service="file", path=str(empty_file))
    assert data == {}


def test_load_dotenv_service_file_nonexistent():
    """load_dotenv(service="file", path=nonexistent) loads nothing and returns False."""
    result = load_dotenv(service="file", path="/nonexistent/sdk/env.file")
    assert result is False


def test_dotenv_values_service_local_explicit(mock_keyring, sample_env):
    """dotenv_values(service="local") with project/domain returns keychain dict."""
    from click.testing import CliRunner

    from enveloper.cli import cli

    runner = CliRunner()
    runner.invoke(cli, ["--project", "test", "-d", "aws", "import", str(sample_env)])
    data = dotenv_values(project="test", domain="aws", service="local")
    assert data.get("TWILIO_API_SID") == "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    assert data.get("AWS_PROFILE") == "default"
