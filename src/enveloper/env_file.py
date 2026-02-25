"""Parse .env files into key-value dicts.

Handles:
  - blank lines and ``#`` comments
  - ``export KEY=VALUE`` prefix
  - single- and double-quoted values (quotes stripped)
  - inline comments after unquoted values
  - values with ``=`` in them (only first ``=`` splits)
"""

from __future__ import annotations

import re
from pathlib import Path

_LINE_RE = re.compile(
    r"""
    ^\s*
    (?:export\s+)?      # optional export prefix
    ([A-Za-z_]\w*)      # key
    \s*=\s*             # separator
    (.*)                # raw value (parsed below)
    $
    """,
    re.VERBOSE,
)


def parse_env_file(path: str | Path) -> dict[str, str]:
    """Read a .env file and return an ordered dict of key-value pairs."""
    result: dict[str, str] = {}
    for line in Path(path).read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        m = _LINE_RE.match(stripped)
        if m is None:
            continue
        key = m.group(1)
        raw = m.group(2).strip()
        result[key] = _unquote(raw)
    return result


def _unquote(raw: str) -> str:
    """Strip surrounding quotes and handle inline comments."""
    if len(raw) >= 2:
        if (raw[0] == '"' and raw[-1] == '"') or (raw[0] == "'" and raw[-1] == "'"):
            return raw[1:-1]
    # Unquoted value: strip inline comment (but not inside the value if # follows a space)
    if " #" in raw:
        raw = raw[: raw.index(" #")].rstrip()
    return raw
