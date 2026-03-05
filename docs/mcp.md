# MCP server: full access to enveloper from LLMs

The **Model Context Protocol (MCP)** lets applications expose context and tools to LLMs in a standard way. Enveloper’s optional **MCP server** gives an LLM agent **full parity with the CLI**: read and write environment variables from the local keychain or remote secret managers (AWS, GCP, Azure, Vault, GitHub, etc.) **without** loading a `.env` file in the repo.

## Install

```bash
pip install enveloper[mcp]
```

Or with uv:

```bash
uv pip install enveloper[mcp]
```

For cloud stores, add the right extra, e.g. `pip install enveloper[mcp,aws]`.

## Run the server

The server uses **stdio** (for IDE integration):

```bash
enveloper-mcp
```

Or:

```bash
uv run python -m enveloper.mcp_server
```

The MCP client (Cursor, Claude Desktop, etc.) spawns this command and talks over stdin/stdout.

## Tools exposed to LLMs (full CLI parity)

An LLM can do everything you can do via the enveloper CLI. Tools are described in human-friendly terms (e.g. get secret, list keys, set secret, export env). In code you call them as `get_secret()`, `list_keys()`, and so on; error messages are also human-friendly (e.g. "Secret not found", "File not found").

### Read

| Tool (API name) | What it does |
|-----------------|--------------|
| **get_secret** (get secret) | Get a secret value by key. Parameters: `key`, optional `domain`, `project`, `version`, `service`, `path`. |
| **list_keys** (list keys) | List key names (no values) for a scope. Parameters: optional `domain`, `project`, `version`, `service`, `path`. |
| **list_domains** (list domains) | List domain names that have secrets. Parameters: optional `project`, `service`. |
| **list_projects** (list projects) | List project names for a domain. Parameters: optional `domain`, `project`, `service`. |
| **list_services** (list services) | List available store names (keychain, file, aws, gcp, azure, vault, github, …). |
| **export_env** (export env) | Export all secrets for the scope as env lines. Parameters: optional `domain`, `project`, `version`, `service`, `path`; `format`: `"dotenv"` or `"unix"`. |
| **unexport_env** (unexport env) | Output shell `unset` (or PowerShell) commands for all variables in the scope. Parameters: optional `domain`, `project`, `version`, `service`, `path`; `format`: `"unix"` or `"win"`. |

### Write

| Tool (API name) | What it does |
|----------------|--------------|
| **set_secret** (set secret) | Set a secret. Parameters: `key`, `value`, optional `domain`, `project`, `version`, `service`, `path`. |
| **delete_secret** (delete secret) | Remove a secret. Parameters: `key`, optional `domain`, `project`, `version`, `service`, `path`. |
| **import_from_file** (import from file) | Import key-value pairs from a .env file into the store. Parameters: `file_path`, optional `domain`, `project`, `version`, `service`, `path`. |
| **clear_scope** (clear scope) | Clear all secrets for a domain/project. Parameters: optional `domain`, `project`, `service`, `path`; `clear_all=True` to clear every secret. No confirmation. |
| **push_to_service** (push to service) | Push secrets from a source store (default: local) to a cloud store. Parameters: `cloud_service` (aws, github, gcp, azure, vault, aliyun), optional `from_service`, `domain`, `project`, `path`. |
| **pull_from_service** (pull from service) | Pull secrets from a cloud store into a target store (default: local). Parameters: `cloud_service`, optional `to_service`, `domain`, `project`, `path`. |

All optional parameters default from **ENVELOPER_DOMAIN**, **ENVELOPER_PROJECT**, **ENVELOPER_VERSION**, **ENVELOPER_SERVICE**, and **.enveloper.toml** (see [Config/Env Overrides](config-env-overrides.md)).

## Step-by-step setup

1. **Install:** `pip install enveloper[mcp]` (and e.g. `[aws]` if you use AWS).
2. **Secrets:** Import into keychain with `enveloper import sample.env -d mydomain -p myproject`, or use a `.env` file and pass `service="file"` and `path` to tools.
3. **Run server:** Your MCP client will run `enveloper-mcp` (or `uv run python -m enveloper.mcp_server`). No need to run it manually.
4. **Configure client:** In Cursor: **Settings → MCP**, add server with command `enveloper-mcp` and empty args. If not on PATH, use command `uv`, args `["run", "python", "-m", "enveloper.mcp_server"]`, and set `cwd` to your project root.
5. **Use tools:** The LLM can get a secret, list keys, export env, etc. For example: `get_secret(key="MY_API_KEY", domain="mydomain", project="myproject")` or `list_keys(service="file", path="/path/to/.env")`.

See [examples/mcp/README.md](../examples/mcp/README.md) and [examples/mcp/STEP_BY_STEP.md](../examples/mcp/STEP_BY_STEP.md) for detailed steps and Cursor config samples.

## Configuring your IDE or MCP client

### Cursor

Add the enveloper MCP server (e.g. **Settings → MCP** or `.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "enveloper": {
      "command": "enveloper-mcp",
      "args": []
    }
  }
}
```

If `enveloper-mcp` is not on PATH, use the project directory and uv:

```json
{
  "mcpServers": {
    "enveloper": {
      "command": "uv",
      "args": ["run", "python", "-m", "enveloper.mcp_server"],
      "cwd": "/path/to/your/enveloper-py"
    }
  }
}
```

### Claude Desktop / other MCP clients

Register a server with command `enveloper-mcp` (or the uv variant) and **stdio** transport. See your client’s documentation.

## Using the file store

To use a `.env` file instead of the keychain, pass `service="file"` and `path` to the tools, e.g.:

- `get_secret(key="MY_API_KEY", service="file", path="/path/to/.env")`
- `set_secret(key="X", value="y", service="file", path="/path/to/.env")`
- `list_keys(service="file", path="/path/to/.env")`

You can set **ENVELOPER_SERVICE=file** and **ENVELOPER_PATH** (if your client supports env) so the LLM doesn’t need to pass them every time.

## Examples and tests

- **Runnable demo:** From the repo root, run `uv run python examples/mcp/demo_tools.py`. This script calls the same MCP tool functions (get secret, list keys, export env) an LLM would use, with the file store and `examples/mcp/demo.env`.
- **Tests:** Run `uv run pytest tests/test_mcp.py -v` for MCP tool and server tests, and `uv run pytest tests/test_examples.py -v -k mcp` for example-docs and demo checks.

See [examples/mcp/README.md](../examples/mcp/README.md) for install, use, and step-by-step instructions.

## Security

- The MCP server has **full read and write** access to the configured stores (keychain, file, or cloud). The LLM can get a secret, set a secret, list keys, export env, import from file, clear scope, push to service, and pull from service.
- Run it only in a **trusted environment**. Any process that can start the server can read and change secrets for the scopes allowed by your ENVELOPER_* and config.
- For cloud stores, the server uses your existing credentials (env vars, config, default chain). Restrict who can spawn the MCP server.

## See also

- [LLM / AI assistant guide](llm.md) — How LLMs work on this repo (including MCP).
- [Domains, projects & versioning](domains-projects-versioning.md) — How domain/project/version scope secrets.
- [Service Backend](service-backend.md) — Choosing keychain, file, or cloud store.
- [examples/mcp](../examples/mcp/) — Runnable example and step-by-step instructions.
