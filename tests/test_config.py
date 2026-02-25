"""Tests for .enveloper.toml config loading."""

from __future__ import annotations

from enveloper.config import EnveloperConfig, load_config


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


def test_load_config_defaults():
    cfg = load_config(path=None)
    assert cfg.project == "default"
    assert cfg.aws_profile == "default"
    assert cfg.github_prefix == ""


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
