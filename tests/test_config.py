"""Tests for .enveloper.toml config loading."""

from __future__ import annotations

from pathlib import Path

import pytest

from enveloper.config import EnveloperConfig, find_config_file, load_config


def test_load_config_invalid_toml_syntax(tmp_path):
    """Invalid TOML syntax in project file raises when loading config."""
    toml = tmp_path / ".enveloper.toml"
    toml.write_text("[enveloper\nproject = \"x\"")  # unclosed bracket
    with pytest.raises(ValueError):  # TOMLDecodeError subclasses ValueError
        load_config(toml)


def test_load_config_malformed_domains_not_table(tmp_path):
    """Project file with enveloper.domains not a table raises when loading config."""
    toml = tmp_path / ".enveloper.toml"
    toml.write_text("""\
[enveloper]
project = "myproj"
domains = "not-a-table"
""")
    with pytest.raises(AttributeError):
        load_config(toml)


def test_load_config_from_file(tmp_path):
    toml = tmp_path / ".enveloper.toml"
    toml.write_text("""\
[enveloper]
project = "myproj"

[enveloper.domains.aws]
env_file = "cloud/aws/.env"
ssm_prefix = "/myproj/{env}/"

[enveloper.aws]
profile = "custom"
region = "eu-west-1"

[enveloper.github]
prefix = "MYPROJ_"
""")
    cfg = load_config(toml)
    assert cfg.project == "myproj"
    assert cfg.aws_profile == "custom"
    assert cfg.aws_region == "eu-west-1"
    assert cfg.github_prefix == "MYPROJ_"
    assert "aws" in cfg.domains
    assert cfg.domains["aws"].env_file == "cloud/aws/.env"
    assert cfg.domains["aws"].ssm_prefix == "/myproj/{env}/"


def test_load_config_defaults(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    cfg = load_config(path=None)
    assert cfg.project == "_default_"
    assert cfg.service is None
    assert cfg.aws_profile == "default"
    assert cfg.github_prefix == ""
    assert cfg.vault_url is None
    assert cfg.vault_mount == "secret"


def test_find_config_file_prefers_user_enveloper_dir(monkeypatch, tmp_path):
    """When ~/.enveloper exists and contains .enveloper.toml, it is preferred over cwd."""
    home = tmp_path / "home"
    home.mkdir()
    user_dir = home / ".enveloper"
    user_dir.mkdir()
    user_config = user_dir / ".enveloper.toml"
    user_config.write_text('[enveloper]\nproject = "from-home"\n')
    monkeypatch.setattr(Path, "home", lambda: home)

    # cwd has a config too
    cwd = tmp_path / "project"
    cwd.mkdir()
    cwd_config = cwd / ".enveloper.toml"
    cwd_config.write_text('[enveloper]\nproject = "from-cwd"\n')
    monkeypatch.chdir(cwd)

    found = find_config_file()
    assert found is not None
    assert found == user_config
    cfg = load_config()
    assert cfg.project == "from-home"


def test_find_config_file_falls_back_to_cwd_when_user_dir_missing(monkeypatch, tmp_path):
    """When ~/.enveloper does not exist, search upward from cwd."""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr(Path, "home", lambda: home)
    # no ~/.enveloper

    cwd = tmp_path / "project"
    cwd.mkdir()
    cwd_config = cwd / ".enveloper.toml"
    cwd_config.write_text('[enveloper]\nproject = "from-cwd"\n')
    monkeypatch.chdir(cwd)

    found = find_config_file()
    assert found == cwd_config
    cfg = load_config()
    assert cfg.project == "from-cwd"


def test_load_config_service(tmp_path):
    """Config can set default service (e.g. for CLI/SDK resolution)."""
    toml = tmp_path / ".enveloper.toml"
    toml.write_text("""\
[enveloper]
project = "myproj"
service = "file"
""")
    cfg = load_config(toml)
    assert cfg.project == "myproj"
    assert cfg.service == "file"


def test_load_config_vault_section(tmp_path):
    toml = tmp_path / ".enveloper.toml"
    toml.write_text("""\
[enveloper]
project = "p"
[enveloper.vault]
url = "https://vault.example.com"
mount = "my-mount"
""")
    cfg = load_config(toml)
    assert cfg.vault_url == "https://vault.example.com"
    assert cfg.vault_mount == "my-mount"


def test_load_config_gcp_section(tmp_path):
    toml = tmp_path / ".enveloper.toml"
    toml.write_text("""\
[enveloper]
project = "p"
[enveloper.gcp]
project = "my-gcp-project"
""")
    cfg = load_config(toml)
    assert cfg.gcp_project == "my-gcp-project"


def test_load_config_azure_section(tmp_path):
    toml = tmp_path / ".enveloper.toml"
    toml.write_text("""\
[enveloper]
project = "p"
[enveloper.azure]
vault_url = "https://my-vault.vault.azure.net/"
""")
    cfg = load_config(toml)
    assert cfg.azure_vault_url == "https://my-vault.vault.azure.net/"


def test_load_config_aliyun_section(tmp_path):
    toml = tmp_path / ".enveloper.toml"
    toml.write_text("""\
[enveloper]
project = "p"
[enveloper.aliyun]
region_id = "cn-shanghai"
access_key_id = "key"
access_key_secret = "secret"
""")
    cfg = load_config(toml)
    assert cfg.aliyun_region_id == "cn-shanghai"
    assert cfg.aliyun_access_key_id == "key"
    assert cfg.aliyun_access_key_secret == "secret"


def test_resolve_ssm_prefix():
    from enveloper.config import DomainConfig

    cfg = EnveloperConfig(
        project="test",
        domains={"aws": DomainConfig(ssm_prefix="/test/{env}/")},
    )
    assert cfg.resolve_ssm_prefix("aws", "prod") == "/test/prod/"


def test_resolve_ssm_prefix_missing_domain():
    cfg = EnveloperConfig(project="test")
    assert cfg.resolve_ssm_prefix("nope") is None
