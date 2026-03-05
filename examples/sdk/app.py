#!/usr/bin/env python3
"""Sample app: load secrets via the enveloper SDK (no .env file required at runtime).

Uses load_dotenv() to populate os.environ and dotenv_values() to get a dict.
Domain/project can be set via ENVELOPER_DOMAIN / ENVELOPER_PROJECT or passed explicitly.
"""
from __future__ import annotations

import os

from enveloper import dotenv_values, load_dotenv


def main() -> None:
    domain = os.environ.get("ENVELOPER_DOMAIN", "mydomain")
    project = os.environ.get("ENVELOPER_PROJECT", "myproject")

    # Option 1: load into process environment (good for scripts and subprocesses)
    load_dotenv(domain=domain, project=project)
    api_key = os.environ.get("MY_API_KEY")
    level = os.environ.get("LEVEL_SET")

    # Option 2: get a dict without modifying os.environ (good for passing to functions)
    secrets = dotenv_values(domain=domain, project=project)
    secret_val = secrets.get("MY_API_SECRET", "(not set)")

    print("Secrets loaded via enveloper SDK (no .env file):")
    print(f"  MY_API_KEY: {'set' if api_key else '(not set)'} (length {len(api_key or '')})")
    print(f"  LEVEL_SET: {level or '(not set)'}")
    print(f"  MY_API_SECRET: {'set' if secrets.get('MY_API_SECRET') else '(not set)'}")
    print("Done.")


if __name__ == "__main__":
    main()
