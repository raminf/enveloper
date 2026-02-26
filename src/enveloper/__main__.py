"""Entry point for the enveloper CLI (run via ``enveloper``, ``envr``, or ``python -m enveloper``)."""

from __future__ import annotations

import sys


def main() -> None:
    """Run the CLI."""
    try:
        from enveloper.cli import cli
    except ImportError:
        sys.stderr.write("Enveloper CLI dependencies missing. Install with: pip install enveloper\n")
        sys.exit(1)
    cli()


if __name__ == "__main__":
    main()
