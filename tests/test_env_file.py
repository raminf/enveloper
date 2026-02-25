"""Tests for .env file parser."""

from __future__ import annotations

from enveloper.env_file import parse_env_file


def test_parse_standard_env(sample_env):
    result = parse_env_file(sample_env)
    assert result["AWS_PROFILE"] == "default"
    assert result["TWILIO_API_SID"] == "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"


def test_parse_double_quoted(sample_env):
    result = parse_env_file(sample_env)
    assert result["TWILIO_AUTH_TOKEN"] == "my secret token"


def test_parse_single_quoted(sample_env):
    result = parse_env_file(sample_env)
    assert result["SINGLE_QUOTED"] == "hello world"


def test_parse_export_prefix(sample_env):
    result = parse_env_file(sample_env)
    assert result["MESSAGING_PROVIDER"] == "twilio"


def test_parse_inline_comment(sample_env):
    result = parse_env_file(sample_env)
    assert result["INLINE_COMMENT"] == "some_value"


def test_parse_empty_value(sample_env):
    result = parse_env_file(sample_env)
    assert result["EMPTY_VALUE"] == ""


def test_parse_equals_in_value(sample_env):
    result = parse_env_file(sample_env)
    assert result["EQUALS_IN_VALUE"] == "postgres://user:pass@host/db?opt=1"


def test_comments_and_blank_lines_skipped(sample_env):
    result = parse_env_file(sample_env)
    assert len(result) == 8


def test_empty_file(tmp_path):
    p = tmp_path / "empty.env"
    p.write_text("")
    assert parse_env_file(p) == {}


def test_comments_only(tmp_path):
    p = tmp_path / "comments.env"
    p.write_text("# just a comment\n# another\n")
    assert parse_env_file(p) == {}


def test_malformed_lines_skipped(tmp_path):
    p = tmp_path / "bad.env"
    p.write_text("GOOD=value\nno_equals\n=missing_key\n123BAD=nope\n")
    result = parse_env_file(p)
    assert result == {"GOOD": "value"}
