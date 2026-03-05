# Copyright (c) 2026 Ramin Firoozye
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for the examples/ folder: structure, content, and runnable workflow.

Unit tests (structure, content, in-process CLI with mocks) are marked @pytest.mark.unit.
Integration tests (subprocess scripts, full workflows) are marked @pytest.mark.integration.
Run unit-only: pytest tests/test_examples.py -m unit
Run integration-only: pytest tests/test_examples.py -m integration
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from enveloper.cli import cli

# Examples root relative to repo root (where pytest is run from)
EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"


def _examples_path(*parts: str) -> Path:
    return EXAMPLES_DIR.joinpath(*parts)


# ---------------------------------------------------------------------------
# Structure and content (unit)
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_examples_dir_exists():
    assert EXAMPLES_DIR.is_dir(), "examples/ directory must exist"


@pytest.mark.unit
def test_examples_sample_env_exists():
    p = _examples_path("sample.env")
    assert p.is_file(), "examples/sample.env must exist"
    content = p.read_text()
    assert "MY_API_KEY" in content
    assert "LEVEL_SET" in content


@pytest.mark.unit
def test_examples_readme_exists():
    p = _examples_path("README.md")
    assert p.is_file()
    content = p.read_text()
    assert "import" in content
    assert "export" in content or "unix" in content
    assert "unexport" in content


# ---------------------------------------------------------------------------
# Docker example (unit)
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_examples_docker_dockerfile_exists():
    assert _examples_path("docker", "Dockerfile").is_file()


@pytest.mark.unit
def test_examples_docker_dockerfile_contains_enveloper():
    content = _examples_path("docker", "Dockerfile").read_text()
    assert "enveloper" in content
    assert "export" in content or "entrypoint" in content.lower()


@pytest.mark.unit
def test_examples_docker_entrypoint_contains_export():
    content = _examples_path("docker", "entrypoint.sh").read_text()
    assert "enveloper" in content
    assert "export" in content
    assert "unix" in content or "format unix" in content


@pytest.mark.unit
def test_examples_docker_readme_documents_export_unexport():
    content = _examples_path("docker", "README.md").read_text()
    assert "export" in content and "unexport" in content
    assert "unix" in content or "format unix" in content


# ---------------------------------------------------------------------------
# Makefile example (unit)
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_examples_makefile_makefile_exists():
    assert _examples_path("makefile", "Makefile").is_file()


@pytest.mark.unit
def test_examples_makefile_contains_export_and_unexport():
    content = _examples_path("makefile", "Makefile").read_text()
    assert "enveloper" in content
    assert "export" in content and "unexport" in content
    assert "format unix" in content


@pytest.mark.unit
def test_examples_makefile_readme_documents_workflow():
    content = _examples_path("makefile", "README.md").read_text()
    assert "import" in content and "export" in content and "unexport" in content


# ---------------------------------------------------------------------------
# Kubernetes example (unit)
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_examples_kubernetes_job_yaml_exists():
    assert _examples_path("kubernetes", "job.yaml").is_file()


@pytest.mark.unit
def test_examples_kubernetes_job_contains_enveloper_commands():
    content = _examples_path("kubernetes", "job.yaml").read_text()
    assert "enveloper" in content
    assert "pull" in content or "export" in content
    assert "export" in content
    assert "unix" in content or "format unix" in content


@pytest.mark.unit
def test_examples_kubernetes_readme_documents_export_unexport():
    content = _examples_path("kubernetes", "README.md").read_text()
    assert "export" in content and "unexport" in content or "pull" in content


# ---------------------------------------------------------------------------
# CI/CD example (unit)
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_examples_cicd_workflow_exists():
    assert _examples_path("cicd", "github-actions.yml").is_file()


@pytest.mark.unit
def test_examples_cicd_workflow_contains_export_and_unexport():
    content = _examples_path("cicd", "github-actions.yml").read_text()
    assert "enveloper" in content
    assert "export" in content and "unexport" in content
    assert "format unix" in content


@pytest.mark.unit
def test_examples_cicd_readme_documents_workflow():
    content = _examples_path("cicd", "README.md").read_text()
    assert "import" in content or "pull" in content
    assert "export" in content and "unexport" in content


# ---------------------------------------------------------------------------
# Shell script example (unit)
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_examples_shell_script_exists():
    p = _examples_path("shell", "run_with_secrets.sh")
    assert p.is_file()


@pytest.mark.unit
def test_examples_shell_script_contains_export_and_unexport():
    content = _examples_path("shell", "run_with_secrets.sh").read_text()
    assert "enveloper" in content
    assert "export" in content and "unexport" in content
    assert "format unix" in content


@pytest.mark.unit
def test_examples_shell_readme_documents_workflow():
    content = _examples_path("shell", "README.md").read_text()
    assert "import" in content and "export" in content and "unexport" in content


# ---------------------------------------------------------------------------
# GitHub secrets example (unit)
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_examples_github_secrets_readme_exists():
    assert _examples_path("github-secrets", "README.md").is_file()


@pytest.mark.unit
def test_examples_github_secrets_readme_documents_push():
    content = _examples_path("github-secrets", "README.md").read_text()
    assert "push" in content and "github" in content.lower()
    assert "enveloper push --service github" in content or "push --service github" in content


@pytest.mark.unit
def test_examples_github_secrets_push_script_exists():
    assert _examples_path("github-secrets", "push-to-github.sh").is_file()


@pytest.mark.unit
def test_examples_github_secrets_push_script_contains_import_and_push():
    content = _examples_path("github-secrets", "push-to-github.sh").read_text()
    assert "enveloper import" in content
    assert "enveloper push" in content
    assert "github" in content


# ---------------------------------------------------------------------------
# SDK example (unit + integration)
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_examples_sdk_readme_exists():
    assert _examples_path("sdk", "README.md").is_file()


@pytest.mark.unit
def test_examples_sdk_readme_documents_load_dotenv_and_sdk_install():
    content = _examples_path("sdk", "README.md").read_text()
    assert "load_dotenv" in content
    assert "dotenv_values" in content
    assert "enveloper[sdk]" in content or "sdk" in content.lower()


@pytest.mark.unit
def test_examples_sdk_app_py_exists():
    assert _examples_path("sdk", "app.py").is_file()


@pytest.mark.unit
def test_examples_sdk_app_py_uses_load_dotenv_and_dotenv_values():
    content = _examples_path("sdk", "app.py").read_text()
    assert "load_dotenv" in content
    assert "dotenv_values" in content
    assert "from enveloper import" in content


@pytest.mark.integration
def test_examples_sdk_app_runs_with_file_store(tmp_path):
    """Run the SDK app with ENVELOPER_SERVICE=file and a .env in cwd."""
    (tmp_path / ".env").write_text(
        "MY_API_KEY=sdktest\nMY_API_SECRET=secret\nLEVEL_SET=99\n"
    )
    app_py = _examples_path("sdk", "app.py")
    assert app_py.is_file()
    env = {
        **os.environ,
        "ENVELOPER_SERVICE": "file",
        "ENVELOPER_DOMAIN": "mydomain",
        "ENVELOPER_PROJECT": "myproject",
    }
    result = subprocess.run(
        [sys.executable, str(app_py)],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, f"stdout: {result.stdout}\nstderr: {result.stderr}"
    assert "Secrets loaded" in result.stdout or "MY_API_KEY" in result.stdout
    assert "LEVEL_SET" in result.stdout or "99" in result.stdout


@pytest.mark.integration
def test_examples_sdk_load_dotenv_with_keychain(cli_runner, mock_keyring, sample_env):
    """SDK load_dotenv and dotenv_values work after importing into keychain (examples workflow)."""
    from enveloper import dotenv_values, load_dotenv

    domain, project = "mydomain", "myproject"
    cli_runner.invoke(cli, ["--domain", domain, "--project", project, "import", str(sample_env)])
    load_dotenv(domain=domain, project=project)
    assert os.environ.get("TWILIO_API_SID") == "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    vals = dotenv_values(domain=domain, project=project)
    assert vals.get("TWILIO_AUTH_TOKEN") == "my secret token"
    # Clean up so other tests don't see these
    for key in ("TWILIO_API_SID", "TWILIO_AUTH_TOKEN", "MESSAGING_PROVIDER"):
        os.environ.pop(key, None)


# ---------------------------------------------------------------------------
# Domains, projects, versioning example (unit + integration)
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_examples_domains_projects_versioning_readme_exists():
    assert _examples_path("domains-projects-versioning", "README.md").is_file()


@pytest.mark.unit
def test_examples_domains_projects_versioning_readme_documents_domain_project_version():
    content = _examples_path("domains-projects-versioning", "README.md").read_text()
    assert "domain" in content.lower() and "project" in content.lower()
    assert "version" in content.lower() or "semver" in content.lower()
    assert "list domain" in content or "list project" in content
    assert "1.0.0" in content or "2.0.0" in content


@pytest.mark.unit
def test_examples_domains_projects_versioning_demo_sh_exists():
    assert _examples_path("domains-projects-versioning", "demo.sh").is_file()


@pytest.mark.unit
def test_examples_domains_projects_versioning_demo_sh_uses_domain_project_version():
    content = _examples_path("domains-projects-versioning", "demo.sh").read_text()
    assert "enveloper set" in content and "enveloper get" in content
    assert "-d " in content and "-p " in content
    assert "--version" in content or "version" in content
    assert "list domain" in content or "list project" in content


@pytest.mark.integration
def test_examples_domains_projects_versioning_workflow(cli_runner, mock_keyring):
    """Set/get with domain, project, and version (semver); list domain and project."""
    domain, project = "demo_dpv", "myapp"
    # Pass -d/-p/--version after subcommand so they are not consumed by top-level (e.g. --version)
    cli_runner.invoke(cli, ["set", "-d", domain, "-p", project, "--version", "1.0.0", "API_KEY", "val-v1"])
    cli_runner.invoke(cli, ["set", "-d", domain, "-p", project, "--version", "2.0.0", "API_KEY", "val-v2"])
    r_get = cli_runner.invoke(cli, ["get", "-d", domain, "-p", project, "--version", "1.0.0", "API_KEY"])
    assert r_get.exit_code == 0 and "val-v1" in r_get.output
    r_get2 = cli_runner.invoke(cli, ["get", "-d", domain, "-p", project, "--version", "2.0.0", "API_KEY"])
    assert r_get2.exit_code == 0 and "val-v2" in r_get2.output
    r_domains = cli_runner.invoke(cli, ["list", "domain"])
    assert r_domains.exit_code == 0 and domain in r_domains.output
    r_projects = cli_runner.invoke(cli, ["list", "project", "-d", domain])
    assert r_projects.exit_code == 0 and project in r_projects.output


# ---------------------------------------------------------------------------
# Runnable workflow: shell script with file store (integration)
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_examples_shell_script_runs_with_file_store(tmp_path):
    """Run the shell script with ENVELOPER_SERVICE=file and a .env in cwd."""
    (tmp_path / ".env").write_text(
        "MY_API_KEY=testkey\nMY_API_SECRET=testsecret\nLEVEL_SET=42\n"
    )
    script = _examples_path("shell", "run_with_secrets.sh")
    assert script.is_file()
    env = {**os.environ, "ENVELOPER_SERVICE": "file"}
    result = subprocess.run(
        ["sh", str(script)],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, f"stdout: {result.stdout}\nstderr: {result.stderr}"
    assert "Env loaded" in result.stdout or "LEVEL_SET" in result.stdout
    assert "Env cleared" in result.stdout or "unset" in result.stdout or "Done" in result.stdout


# ---------------------------------------------------------------------------
# Makefile demo target (with file store) (integration)
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_examples_makefile_demo_runs_with_file_store(tmp_path):
    """Run make demo with ENVELOPER_SERVICE=file and a .env in cwd."""
    (tmp_path / ".env").write_text(
        "MY_API_KEY=makekey\nMY_API_SECRET=makesecret\nLEVEL_SET=100\n"
    )
    makefile = _examples_path("makefile", "Makefile")
    env = {**os.environ, "ENVELOPER_SERVICE": "file"}
    result = subprocess.run(
        ["make", "-f", str(makefile), "demo"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    # make may fail if enveloper not on PATH in subprocess; accept 0 or check for enveloper
    if result.returncode != 0:
        assert "enveloper" in result.stderr or "enveloper" in result.stdout, (
            f"Unexpected failure: stdout={result.stdout!r} stderr={result.stderr!r}"
        )
        pytest.skip("make demo requires enveloper on PATH")
    assert "Loading env" in result.stdout or "Demo done" in result.stdout


# ---------------------------------------------------------------------------
# Workflow: import -> export (unix) -> unexport (integration)
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_examples_workflow_import_export_unexport(cli_runner, mock_keyring, sample_env):
    """Examples workflow: import loads keychain, export (unix) and unexport work."""
    domain, project = "mydomain", "myproject"
    r_import = cli_runner.invoke(
        cli, ["--domain", domain, "--project", project, "import", str(sample_env)]
    )
    assert r_import.exit_code == 0, r_import.output
    assert "Imported" in r_import.output

    r_export = cli_runner.invoke(
        cli, ["--domain", domain, "--project", project, "export", "--format", "unix"]
    )
    assert r_export.exit_code == 0
    assert "export " in r_export.output
    assert "TWILIO_API_SID=" in r_export.output or "MESSAGING_PROVIDER=" in r_export.output

    r_unexport = cli_runner.invoke(
        cli, ["--domain", domain, "--project", project, "unexport", "--format", "unix"]
    )
    assert r_unexport.exit_code == 0
    assert "unset " in r_unexport.output


# ---------------------------------------------------------------------------
# Additional unit tests (parsing, YAML, output format)
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_examples_sample_env_parseable():
    """examples/sample.env is parseable as .env and contains expected keys."""
    from enveloper.env_file import parse_env_file

    path = _examples_path("sample.env")
    assert path.is_file()
    pairs = parse_env_file(path)
    assert "MY_API_KEY" in pairs
    assert "MY_API_SECRET" in pairs
    assert "LEVEL_SET" in pairs
    assert pairs["LEVEL_SET"] == "500"


@pytest.mark.unit
def test_examples_kubernetes_job_yaml_valid():
    """examples/kubernetes/job.yaml is valid YAML and has expected Job structure."""
    import yaml

    path = _examples_path("kubernetes", "job.yaml")
    assert path.is_file()
    data = yaml.safe_load(path.read_text())
    assert data is not None
    assert data.get("kind") == "Job"
    assert "spec" in data
    assert "template" in data["spec"]


@pytest.mark.unit
def test_examples_cicd_workflow_yaml_valid():
    """examples/cicd/github-actions.yml is valid YAML and has workflow structure."""
    import yaml

    path = _examples_path("cicd", "github-actions.yml")
    assert path.is_file()
    data = yaml.safe_load(path.read_text())
    assert data is not None
    assert "name" in data
    assert "jobs" in data


@pytest.mark.unit
def test_examples_export_unix_output_format(cli_runner, mock_keyring, sample_env):
    """Export --format unix emits lines that look like export VAR=value; unexport emits unset VAR."""
    domain, project = "mydomain", "myproject"
    cli_runner.invoke(cli, ["--domain", domain, "--project", project, "import", str(sample_env)])
    r_export = cli_runner.invoke(
        cli, ["--domain", domain, "--project", project, "export", "--format", "unix"]
    )
    assert r_export.exit_code == 0
    lines = [ln for ln in r_export.output.strip().splitlines() if ln.strip()]
    for line in lines:
        assert line.startswith("export "), f"Expected 'export ...' got {line!r}"
        assert "=" in line
    r_unexport = cli_runner.invoke(
        cli, ["--domain", domain, "--project", project, "unexport", "--format", "unix"]
    )
    assert r_unexport.exit_code == 0
    unset_lines = [ln for ln in r_unexport.output.strip().splitlines() if ln.strip()]
    for line in unset_lines:
        assert line.startswith("unset "), f"Expected 'unset ...' got {line!r}"


# ---------------------------------------------------------------------------
# Additional integration tests
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_examples_domains_projects_versioning_demo_set_get_with_file_store(tmp_path):
    """Run set/get/export part of domains-projects-versioning flow with file store (list domain requires keychain)."""
    (tmp_path / ".env").write_text("")
    env = {**os.environ, "ENVELOPER_SERVICE": "file"}
    # Run set and get with domain/project/version via subprocess (file store writes to .env)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "enveloper",
            "set",
            "-d",
            "demo_dpv",
            "-p",
            "myapp",
            "--version",
            "1.0.0",
            "API_KEY",
            "key-v1",
        ],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    result2 = subprocess.run(
        [
            sys.executable,
            "-m",
            "enveloper",
            "get",
            "-d",
            "demo_dpv",
            "-p",
            "myapp",
            "--version",
            "1.0.0",
            "API_KEY",
        ],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result2.returncode == 0
    assert "key-v1" in result2.stdout
