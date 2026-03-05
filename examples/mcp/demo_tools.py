#!/usr/bin/env python3
"""Demo: call the same MCP tool functions an LLM would use (get secret, list keys, export env).

Uses the file store and a local .env so you can run without keychain. Install first:
  pip install enveloper[mcp]

Run from repo root:
  uv run python examples/mcp/demo_tools.py
Or from this directory:
  uv run python demo_tools.py
"""
from __future__ import annotations

import os
from pathlib import Path

# Resolve path to demo.env next to this script
_SCRIPT_DIR = Path(__file__).resolve().parent
_DEMO_ENV = _SCRIPT_DIR / "demo.env"


def main() -> None:
    if not _DEMO_ENV.is_file():
        print(f"Create {_DEMO_ENV} with a few KEY=value lines, or run from examples/mcp/.")
        return
    path = str(_DEMO_ENV)

    # Use the same tool functions the MCP server exposes to LLMs
    from enveloper.mcp_server import export_env, get_secret, list_keys, list_services

    print("=== MCP tools demo (file store) ===\n")

    print("1. list_services() — available stores:")
    services = list_services()
    print(f"   {services}\n")

    print("2. list_keys(service='file', path=...) — key names:")
    keys = list_keys(service="file", path=path)
    print(f"   {keys}\n")

    print("3. get_secret(key='MY_API_KEY', service='file', path=...) — one value:")
    val = get_secret("MY_API_KEY", service="file", path=path)
    print(f"   {val!r}\n")

    print("4. get_secret (missing key) — human-friendly message:")
    missing = get_secret("MISSING_KEY", service="file", path=path)
    print(f"   {missing!r}\n")

    print("5. export_env(service='file', path=..., format='unix') — shell export lines:")
    exported = export_env(service="file", path=path, format="unix")
    for line in exported.splitlines()[:3]:
        print(f"   {line}")
    if exported.count("\n") >= 3:
        print("   ...")
    print()

    print("Done. An LLM would call these same tools via the MCP server (enveloper-mcp).")


if __name__ == "__main__":
    main()
