# MCP server guidelines for LLMs

The enveloper project runs an **MCP (Model Context Protocol) server** so that **another** LLM (e.g. in Cursor or Claude Desktop) can access environment variables from the user’s local keychain or remote secret manager. The MCP exposes **full CLI parity** with **human-friendly** descriptions and errors (e.g. get secret, list keys, set secret; "Secret not found", "File not found").

## What the enveloper MCP server does

It exposes tools so the LLM can **get a secret**, **list keys**, **list domains**, **list projects**, **list services**, **export env**, **unexport env**, **set a secret**, **delete a secret**, **import from file**, **clear scope**, **push to service**, and **pull from service**. All optional params default from **ENVELOPER_*** and **.enveloper.toml**. API names use underscores (e.g. `get_secret`, `list_keys`); descriptions and error messages are in plain language.

**Read:** get_secret, list_keys, list_domains, list_projects, list_services, export_env, unexport_env.

**Write:** set_secret, delete_secret, import_from_file, clear_scope, push_to_service, pull_from_service.

So an LLM agent can read and write env vars from keychain or cloud in the same way as the CLI.

## Install and run

- **Install:** `pip install enveloper[mcp]` (or `uv pip install enveloper[mcp]`). Add e.g. `[aws]` for cloud.
- **Run:** `enveloper-mcp` (stdio). Or `uv run python -m enveloper.mcp_server`.

The server is started by the MCP client; the user does not need to run it manually.

## Configuring the client

- **Cursor:** Add an MCP server with command `enveloper-mcp` (or `uv` with args `run`, `python`, `-m`, `enveloper.mcp_server` and `cwd` set to the project root). See [docs/mcp.md](../docs/mcp.md) and [examples/mcp/README.md](../examples/mcp/README.md), [examples/mcp/STEP_BY_STEP.md](../examples/mcp/STEP_BY_STEP.md).
- **Other clients:** Use stdio transport and the same command.

## When suggesting MCP

- User wants an LLM agent (or IDE AI) to **access** env vars from enveloper (keychain or cloud) → suggest installing `enveloper[mcp]`, configuring their MCP client with `enveloper-mcp`, and point to **docs/mcp.md** and **examples/mcp/** for step-by-step instructions and full tool list.
- User wants to use a **.env file** only → they can pass `service="file"` and `path="/path/to/.env"` to the tools, or set **ENVELOPER_SERVICE=file** and **ENVELOPER_PATH**.

## Security note

The MCP server has full read/write access. Remind users to run it only in a trusted environment; anyone who can start the server can read and change secrets for the configured scopes.
