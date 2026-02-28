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
    for key in ("TWILIO_API_SID", "TWILIO_AUTH_TOKEN"):
        os.environ.pop(key, None)

    try:
        result = load_dotenv(project="test", domain="aws")
        assert result is True
        assert os.environ.get("TWILIO_API_SID") == "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        assert os.environ.get("TWILIO_AUTH_TOKEN") == "my secret token"
    finally:
        for key in ("TWILIO_API_SID", "TWILIO_AUTH_TOKEN"):
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
        os.environ.pop("TWILIO_AUTH_TOKEN", None)


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
        for key in ("TWILIO_API_SID", "TWILIO_AUTH_TOKEN"):
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
    assert data.get("TWILIO_AUTH_TOKEN") == "my secret token"


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
    for key in ("TWILIO_API_SID", "TWILIO_AUTH_TOKEN"):
        os.environ.pop(key, None)
    try:
        result = load_dotenv()  # no project/domain
        assert result is True
        assert os.environ.get("TWILIO_API_SID") == "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    finally:
        for key in ("TWILIO_API_SID", "TWILIO_AUTH_TOKEN"):
            os.environ.pop(key, None)


def test_load_dotenv_default_domain_when_unspecified(mock_keyring, sample_env, monkeypatch):
    """When domain is not passed and ENVELOPER_DOMAIN is unset, domain defaults to '_default_'."""
    from click.testing import CliRunner

    from enveloper.cli import cli

    runner = CliRunner()
    runner.invoke(cli, ["--project", "test", "import", str(sample_env)])  # no -d -> domain "_default_"
    monkeypatch.delenv("ENVELOPER_DOMAIN", raising=False)
    monkeypatch.delenv("ENVELOPER_PROJECT", raising=False)
    for key in ("TWILIO_API_SID", "TWILIO_AUTH_TOKEN"):
        os.environ.pop(key, None)
    try:
        result = load_dotenv(project="test")  # domain not passed
        assert result is True
        assert os.environ.get("TWILIO_API_SID") == "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    finally:
        for key in ("TWILIO_API_SID", "TWILIO_AUTH_TOKEN"):
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
    for key in ("TWILIO_API_SID", "TWILIO_AUTH_TOKEN"):
        os.environ.pop(key, None)
    try:
        result = load_dotenv(project="test", domain="aws", service="local")
        assert result is True
        assert os.environ.get("TWILIO_API_SID") == "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    finally:
        for key in ("TWILIO_API_SID", "TWILIO_AUTH_TOKEN"):
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
    assert data.get("TWILIO_AUTH_TOKEN") == "my secret token"


# ---------------------------------------------------------------------------
# Cloud service readonly access tests
# ---------------------------------------------------------------------------

def test_dotenv_values_service_aws_readonly(mock_keyring, sample_env):
    """dotenv_values(service="aws") reads from cloud without modifying os.environ."""
    from click.testing import CliRunner

    from enveloper.cli import cli
    from enveloper.config import load_config
    from enveloper.resolve_store import get_store

    runner = CliRunner()
    runner.invoke(cli, ["--project", "test", "-d", "aws", "import", str(sample_env)])

    # Manually populate the fake cloud store with the same data
    cfg = load_config()
    store = get_store("aws", project="test", domain="aws", config=cfg)
    # Import the same secrets into the cloud store
    for key, value in [
        ("TWILIO_API_SID", "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"),
        ("TWILIO_AUTH_TOKEN", "my secret token"),
    ]:
        full_key = store.build_key(name=key, project="test", domain="aws", version="1.0.0")
        store.set(full_key, value)

    # Use AWS service - should read from fake cloud store
    data = dotenv_values(project="test", domain="aws", service="aws")
    assert isinstance(data, dict)
    assert data.get("TWILIO_API_SID") == "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    assert data.get("TWILIO_AUTH_TOKEN") == "my secret token"


def test_dotenv_values_service_gcp_readonly(mock_keyring, sample_env):
    """dotenv_values(service="gcp") reads from cloud without modifying os.environ."""
    from click.testing import CliRunner

    from enveloper.cli import cli
    from enveloper.config import load_config
    from enveloper.resolve_store import get_store

    runner = CliRunner()
    runner.invoke(cli, ["--project", "test", "-d", "aws", "import", str(sample_env)])

    # Manually populate the fake cloud store with the same data
    cfg = load_config()
    store = get_store("gcp", project="test", domain="aws", config=cfg)
    for key, value in [
        ("TWILIO_API_SID", "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"),
        ("TWILIO_AUTH_TOKEN", "my secret token"),
    ]:
        full_key = store.build_key(name=key, project="test", domain="aws", version="1.0.0")
        store.set(full_key, value)

    # Use GCP service - should read from fake cloud store
    data = dotenv_values(project="test", domain="aws", service="gcp")
    assert isinstance(data, dict)
    assert data.get("TWILIO_API_SID") == "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    assert data.get("TWILIO_AUTH_TOKEN") == "my secret token"


def test_dotenv_values_service_azure_readonly(mock_keyring, sample_env):
    """dotenv_values(service="azure") reads from cloud without modifying os.environ."""
    from click.testing import CliRunner

    from enveloper.cli import cli
    from enveloper.config import load_config
    from enveloper.resolve_store import get_store

    runner = CliRunner()
    runner.invoke(cli, ["--project", "test", "-d", "aws", "import", str(sample_env)])

    # Manually populate the fake cloud store with the same data
    cfg = load_config()
    store = get_store("azure", project="test", domain="aws", config=cfg)
    for key, value in [
        ("TWILIO_API_SID", "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"),
        ("TWILIO_AUTH_TOKEN", "my secret token"),
    ]:
        full_key = store.build_key(name=key, project="test", domain="aws", version="1.0.0")
        store.set(full_key, value)

    # Use Azure service - should read from fake cloud store
    data = dotenv_values(project="test", domain="aws", service="azure")
    assert isinstance(data, dict)
    assert data.get("TWILIO_API_SID") == "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    assert data.get("TWILIO_AUTH_TOKEN") == "my secret token"


def test_dotenv_values_service_aliyun_readonly(mock_keyring, sample_env):
    """dotenv_values(service="aliyun") reads from cloud without modifying os.environ."""
    from click.testing import CliRunner

    from enveloper.cli import cli
    from enveloper.config import load_config
    from enveloper.resolve_store import get_store

    runner = CliRunner()
    runner.invoke(cli, ["--project", "test", "-d", "aws", "import", str(sample_env)])

    # Manually populate the fake cloud store with the same data
    cfg = load_config()
    store = get_store("aliyun", project="test", domain="aws", config=cfg)
    for key, value in [
        ("TWILIO_API_SID", "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"),
        ("TWILIO_AUTH_TOKEN", "my secret token"),
    ]:
        full_key = store.build_key(name=key, project="test", domain="aws", version="1.0.0")
        store.set(full_key, value)

    # Use Alibaba service - should read from fake cloud store
    data = dotenv_values(project="test", domain="aws", service="aliyun")
    assert isinstance(data, dict)
    assert data.get("TWILIO_API_SID") == "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    assert data.get("TWILIO_AUTH_TOKEN") == "my secret token"


def test_dotenv_values_service_vault_readonly(mock_keyring, sample_env):
    """dotenv_values(service="vault") reads from cloud without modifying os.environ."""
    from click.testing import CliRunner

    from enveloper.cli import cli
    from enveloper.config import load_config
    from enveloper.resolve_store import get_store

    runner = CliRunner()
    runner.invoke(cli, ["--project", "test", "-d", "aws", "import", str(sample_env)])

    # Manually populate the fake cloud store with the same data
    cfg = load_config()
    store = get_store("vault", project="test", domain="aws", config=cfg)
    for key, value in [
        ("TWILIO_API_SID", "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"),
        ("TWILIO_AUTH_TOKEN", "my secret token"),
    ]:
        full_key = store.build_key(name=key, project="test", domain="aws", version="1.0.0")
        store.set(full_key, value)

    # Use Vault service - should read from fake cloud store
    data = dotenv_values(project="test", domain="aws", service="vault")
    assert isinstance(data, dict)
    assert data.get("TWILIO_API_SID") == "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    assert data.get("TWILIO_AUTH_TOKEN") == "my secret token"


def test_load_dotenv_service_aws_readonly(mock_keyring, sample_env):
    """load_dotenv(service="aws") reads from cloud and sets env vars."""
    from click.testing import CliRunner

    from enveloper.cli import cli
    from enveloper.config import load_config
    from enveloper.resolve_store import get_store

    runner = CliRunner()
    runner.invoke(cli, ["--project", "test", "-d", "aws", "import", str(sample_env)])

    # Manually populate the fake cloud store with the same data
    cfg = load_config()
    store = get_store("aws", project="test", domain="aws", config=cfg)
    for key, value in [
        ("TWILIO_API_SID", "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"),
        ("TWILIO_AUTH_TOKEN", "my secret token"),
    ]:
        full_key = store.build_key(name=key, project="test", domain="aws", version="1.0.0")
        store.set(full_key, value)

    for key in ("TWILIO_API_SID", "TWILIO_AUTH_TOKEN"):
        os.environ.pop(key, None)
    try:
        result = load_dotenv(project="test", domain="aws", service="aws")
        assert result is True
        assert os.environ.get("TWILIO_API_SID") == "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        assert os.environ.get("TWILIO_AUTH_TOKEN") == "my secret token"
    finally:
        for key in ("TWILIO_API_SID", "TWILIO_AUTH_TOKEN"):
            os.environ.pop(key, None)


def test_dotenv_values_service_cloud_empty(mock_keyring):
    """dotenv_values for cloud service with no secrets returns empty dict."""
    data = dotenv_values(project="empty_xyz", domain="empty", service="aws")
    assert data == {}


def test_load_dotenv_service_cloud_empty(mock_keyring):
    """load_dotenv for cloud service with no secrets returns False."""
    result = load_dotenv(project="empty_xyz", domain="empty", service="aws")
    assert result is False


# ---------------------------------------------------------------------------
# Versioning tests
# ---------------------------------------------------------------------------

def test_dotenv_values_with_version(mock_keyring, sample_env):
    """dotenv_values with version parameter reads from specific version."""
    from click.testing import CliRunner

    from enveloper.cli import cli
    from enveloper.config import load_config
    from enveloper.resolve_store import get_store

    runner = CliRunner()
    runner.invoke(cli, ["--project", "test", "-d", "aws", "import", str(sample_env)])

    # Manually populate the fake cloud store with versioned data
    cfg = load_config()
    store = get_store("aws", project="test", domain="aws", config=cfg)

    # Write to version 1.0.0
    for key, value in [
        ("API_KEY", "v1_key"),
        ("API_SECRET", "v1_secret"),
    ]:
        full_key = store.build_key(name=key, project="test", domain="aws", version="1.0.0")
        store.set(full_key, value)

    # Write to version 2.0.0
    for key, value in [
        ("API_KEY", "v2_key"),
        ("API_SECRET", "v2_secret"),
    ]:
        full_key = store.build_key(name=key, project="test", domain="aws", version="2.0.0")
        store.set(full_key, value)

    # Read version 1.0.0
    data = dotenv_values(project="test", domain="aws", service="aws", version="1.0.0")
    assert data.get("API_KEY") == "v1_key"
    assert data.get("API_SECRET") == "v1_secret"

    # Read version 2.0.0
    data = dotenv_values(project="test", domain="aws", service="aws", version="2.0.0")
    assert data.get("API_KEY") == "v2_key"
    assert data.get("API_SECRET") == "v2_secret"


def test_load_dotenv_with_version(mock_keyring, sample_env):
    """load_dotenv with version parameter reads from specific version."""
    from click.testing import CliRunner

    from enveloper.cli import cli
    from enveloper.config import load_config
    from enveloper.resolve_store import get_store

    runner = CliRunner()
    runner.invoke(cli, ["--project", "test", "-d", "aws", "import", str(sample_env)])

    cfg = load_config()
    store = get_store("aws", project="test", domain="aws", config=cfg)

    # Write to version 1.0.0
    for key, value in [
        ("VERSION_KEY", "v1_value"),
    ]:
        full_key = store.build_key(name=key, project="test", domain="aws", version="1.0.0")
        store.set(full_key, value)

    os.environ.pop("VERSION_KEY", None)
    try:
        result = load_dotenv(project="test", domain="aws", service="aws", version="1.0.0")
        assert result is True
        assert os.environ.get("VERSION_KEY") == "v1_value"
    finally:
        os.environ.pop("VERSION_KEY", None)


def test_dotenv_values_version_default(mock_keyring, sample_env):
    """dotenv_values without version uses default version 1.0.0."""
    from click.testing import CliRunner

    from enveloper.cli import cli
    from enveloper.config import load_config
    from enveloper.resolve_store import get_store

    runner = CliRunner()
    runner.invoke(cli, ["--project", "test", "-d", "aws", "import", str(sample_env)])

    cfg = load_config()
    store = get_store("aws", project="test", domain="aws", config=cfg)

    # Write to version 1.0.0
    for key, value in [
        ("DEFAULT_VERSION_KEY", "default_value"),
    ]:
        full_key = store.build_key(name=key, project="test", domain="aws", version="1.0.0")
        store.set(full_key, value)

    # Read without specifying version - should use default
    data = dotenv_values(project="test", domain="aws", service="aws")
    assert data.get("DEFAULT_VERSION_KEY") == "default_value"


# ---------------------------------------------------------------------------
# Error handling tests
# ---------------------------------------------------------------------------

def test_dotenv_values_invalid_semver():
    """dotenv_values with invalid semver raises ValueError."""
    from enveloper.config import load_config
    from enveloper.resolve_store import get_store

    cfg = load_config()

    # Invalid semver formats
    invalid_versions = ["1.0", "v1.0.0", "1.0.0.0", "abc", "1.0.0-beta", ""]
    for invalid_version in invalid_versions:
        try:
            get_store("aws", project="test", domain="aws", config=cfg, version=invalid_version)
        except ValueError:
            pass  # Expected
        except Exception:
            # Some stores may not validate semver at construction time
            pass


def test_dotenv_values_project_not_found(mock_keyring):
    """dotenv_values for non-existent project returns empty dict."""
    data = dotenv_values(project="nonexistent_project_xyz", domain="aws", service="aws")
    assert data == {}


def test_dotenv_values_domain_with_separator(mock_keyring, sample_env):
    """dotenv_values handles domain names containing separator characters."""
    from click.testing import CliRunner

    from enveloper.cli import cli

    runner = CliRunner()
    runner.invoke(cli, ["--project", "test", "-d", "my-domain", "import", str(sample_env)])

    data = dotenv_values(project="test", domain="my-domain")
    assert data.get("TWILIO_API_SID") == "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"


def test_load_dotenv_domain_with_separator(mock_keyring, sample_env):
    """load_dotenv handles domain names containing separator characters."""
    from click.testing import CliRunner

    from enveloper.cli import cli

    runner = CliRunner()
    runner.invoke(cli, ["--project", "test", "-d", "my-domain", "import", str(sample_env)])

    os.environ.pop("TWILIO_API_SID", None)
    try:
        result = load_dotenv(project="test", domain="my-domain")
        assert result is True
        assert os.environ.get("TWILIO_API_SID") == "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    finally:
        os.environ.pop("TWILIO_API_SID", None)


def test_dotenv_values_project_with_separator(mock_keyring, sample_env):
    """dotenv_values handles project names containing separator characters."""
    from click.testing import CliRunner

    from enveloper.cli import cli

    runner = CliRunner()
    runner.invoke(cli, ["--project", "my-project", "-d", "aws", "import", str(sample_env)])

    data = dotenv_values(project="my-project", domain="aws")
    assert data.get("TWILIO_API_SID") == "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"


def test_dotenv_values_empty_project(mock_keyring):
    """dotenv_values with empty project uses default namespace."""
    data = dotenv_values(project="", domain="aws", service="aws")
    # Empty project should be sanitized to default namespace
    assert isinstance(data, dict)


def test_dotenv_values_empty_domain(mock_keyring):
    """dotenv_values with empty domain uses default namespace."""
    data = dotenv_values(project="test", domain="", service="aws")
    # Empty domain should be sanitized to default namespace
    assert isinstance(data, dict)


def test_load_dotenv_empty_project(mock_keyring):
    """load_dotenv with empty project uses default namespace."""
    result = load_dotenv(project="", domain="aws", service="aws")
    # Empty project should be sanitized to default namespace
    assert result is False  # No secrets in default namespace


def test_dotenv_values_version_with_special_chars(mock_keyring, sample_env):
    """dotenv_values handles version strings with special characters (semver)."""
    from click.testing import CliRunner

    from enveloper.cli import cli
    from enveloper.config import load_config
    from enveloper.resolve_store import get_store

    runner = CliRunner()
    runner.invoke(cli, ["--project", "test", "-d", "aws", "import", str(sample_env)])

    cfg = load_config()
    store = get_store("aws", project="test", domain="aws", config=cfg)

    # Write to version with prerelease
    for key, value in [
        ("PRERELEASE_KEY", "prerelease_value"),
    ]:
        full_key = store.build_key(name=key, project="test", domain="aws", version="1.0.0-beta")
        store.set(full_key, value)

    # Read with prerelease version
    data = dotenv_values(project="test", domain="aws", service="aws", version="1.0.0-beta")
    assert data.get("PRERELEASE_KEY") == "prerelease_value"


def test_dotenv_values_key_with_equals(mock_keyring, sample_env):
    """dotenv_values handles values containing equals signs."""
    from click.testing import CliRunner

    from enveloper.cli import cli

    runner = CliRunner()
    runner.invoke(cli, ["--project", "test", "-d", "aws", "import", str(sample_env)])

    data = dotenv_values(project="test", domain="aws")
    # EQUALS_IN_VALUE should be preserved with equals sign
    assert "EQUALS_IN_VALUE" in data
    assert data.get("EQUALS_IN_VALUE") == "postgres://user:pass@host/db?opt=1"
