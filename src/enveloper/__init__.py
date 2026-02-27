# Copyright (c) 2026 Ramin Firoozye
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Enveloper -- manage .env secrets via system keychain with cloud store plugins."""

from enveloper.sdk import dotenv_values, load_dotenv

__all__ = ["__version__", "load_dotenv", "dotenv_values"]
__version__ = "0.1.14"
