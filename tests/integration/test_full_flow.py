"""Full integration flow: clear -> import sample.env -> verify -> export -> push aws -> set -> re-export -> push -> unexport -> clear.

Runs the shared script tests/integration_full_flow.sh (in enveloper-rs) with the Python CLI (enveloper).
Use LOCAL_STORE=file and LOCAL_PATH=/tmp/foo.env to avoid keychain. Set ENVELOPER_TEST_AWS=1 for AWS steps.

From enveloper-py:
  pytest tests/integration/test_full_flow.py -v
  LOCAL_STORE=file LOCAL_PATH=/tmp/env.integration.env pytest tests/integration/test_full_flow.py -v
  ENVELOPER_TEST_AWS=1 pytest tests/integration/test_full_flow.py -v
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

# Script lives in sibling enveloper-rs/tests/ (this file: .../enveloper-py/tests/integration/test_full_flow.py)
_ENVELOPER_PY = Path(__file__).resolve().parent.parent.parent
_ENVELOPER_RS = _ENVELOPER_PY.parent / "enveloper-rs"
_SCRIPT = _ENVELOPER_RS / "tests" / "integration_full_flow.sh"
_SAMPLE_ENV_PY = _ENVELOPER_PY / "sample.env"


@pytest.mark.integration_full_flow
def test_full_flow_with_enveloper():
    """Run the full integration script with the Python enveloper CLI."""
    if not _SCRIPT.exists():
        pytest.skip(f"Integration script not found: {_SCRIPT} (run from workspace with enveloper-rs sibling)")
    if not _SAMPLE_ENV_PY.exists():
        pytest.skip(f"sample.env not found: {_SAMPLE_ENV_PY}")
    env = os.environ.copy()
    env["SAMPLE_ENV"] = str(_SAMPLE_ENV_PY)
    # Use file store so we don't depend on keychain in CI
    if "LOCAL_STORE" not in env:
        import tempfile

        fd, path = tempfile.mkstemp(suffix=".env")
        os.close(fd)
        env["LOCAL_STORE"] = "file"
        env["LOCAL_PATH"] = path
        try:
            result = subprocess.run(
                ["bash", str(_SCRIPT), "enveloper"],
                cwd=str(_ENVELOPER_PY),
                env=env,
                capture_output=True,
                text=True,
                timeout=60,
            )
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass
    else:
        result = subprocess.run(
            ["bash", str(_SCRIPT), "enveloper"],
            cwd=str(_ENVELOPER_PY),
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
        )
    out = result.stdout + result.stderr
    assert result.returncode == 0, f"Script failed:\n{out}"
