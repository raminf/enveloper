# MCP server: let an LLM agent access enveloper (keychain or cloud)

This example shows how to run enveloper’s **MCP server** so that an LLM (e.g. in Cursor or Claude Desktop) can **read and write** environment variables from your local keychain or remote secret manager — the same as using the CLI.

## Step-by-step: get it working

### 1. Install

```bash
pip install enveloper[mcp]
```

Or with uv:

```bash
uv pip install enveloper[mcp]
```

### 2. (Optional) Put some secrets in the keychain

From this repo (examples folder):

```bash
cd examples
enveloper import sample.env --domain mydomain --project myproject
```

Or use the **file** store and a `.env` file: create a `.env` with `MY_API_KEY=secret123` and point the MCP tools at it via `service="file"` and `path` (see below).

### 3. Run the server (for testing)

In a terminal:

```bash
enveloper-mcp
```

Or:

```bash
uv run python -m enveloper.mcp_server
```

The server waits on stdin (stdio). Your MCP client will start it automatically; you don’t need to leave this running.

### 4. Configure your MCP client (e.g. Cursor)

**Option A — `enveloper-mcp` on PATH**

In Cursor: **Settings → MCP** (or edit `.cursor/mcp.json`):

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

**Option B — uv from project directory**

If the command isn’t on PATH, use the project root as `cwd` and run the module:

```json
{
  "mcpServers": {
    "enveloper": {
      "command": "uv",
      "args": ["run", "python", "-m", "enveloper.mcp_server"],
      "cwd": "/absolute/path/to/enveloper-py"
    }
  }
}
```

Replace `/absolute/path/to/enveloper-py` with your repo path.

### 5. Use the tools from the LLM

Once the server is configured, the LLM can **get a secret**, **list keys**, **set a secret**, **export env**, and so on. Tool names in the API use underscores (e.g. `get_secret`); descriptions and errors are human-friendly (e.g. "Secret not found"). Examples:

- **Get a secret (keychain):**  
  `get_secret(key="MY_API_KEY", domain="mydomain", project="myproject")`

- **Get a secret from a .env file:**  
  `get_secret(key="MY_API_KEY", service="file", path="/path/to/.env")`

- **List keys:**  
  `list_keys(domain="mydomain", project="myproject")`

- **Export env (all secrets for a scope):**  
  `export_env(domain="mydomain", project="myproject", format="unix")`

- **Set a secret:**  
  `set_secret(key="NEW_VAR", value="secret", domain="mydomain", project="myproject")`

- **Import from file:**  
  `import_from_file(file_path="/path/to/.env", domain="mydomain", project="myproject")`

- **List services (available backends):**  
  `list_services()` → e.g. `["keychain", "file", "aws", "gcp", ...]`

Defaults for `domain`, `project`, `version`, and `service` come from **ENVELOPER_DOMAIN**, **ENVELOPER_PROJECT**, **ENVELOPER_VERSION**, **ENVELOPER_SERVICE** and **.enveloper.toml**.

## All tools (full CLI parity)

Tools are human-friendly: you can **get a secret**, **list keys**, **set a secret**, **export env**, **import from file**, **clear scope**, **push to service**, **pull from service**. The API uses names like `get_secret`, `list_keys`; error messages use plain language (e.g. "Secret not found", "File not found").

| API name | What it does |
|----------|--------------|
| **get_secret** | Get a secret by key. |
| **set_secret** | Set a secret. |
| **delete_secret** | Remove a secret. |
| **list_keys** | List key names (no values) for a scope. |
| **list_domains** | List domain names. |
| **list_projects** | List project names for a domain. |
| **list_services** | List available stores (keychain, file, aws, gcp, …). |
| **import_from_file** | Import .env file into the store. |
| **export_env** | Export all secrets as dotenv or unix `export` lines. |
| **unexport_env** | Output `unset` (or PowerShell) commands for the scope. |
| **clear_scope** | Clear all secrets for a domain/project (or `clear_all=True`). |
| **push_to_service** | Push from keychain (or other source) to a cloud store (aws, github, …). |
| **pull_from_service** | Pull from a cloud store into keychain (or file). |

So an LLM can do everything you can do via the CLI: read and write env vars from keychain or cloud.

## Using the file store (no keychain)

To point the MCP at a `.env` file instead of the keychain, pass `service="file"` and `path` to the tools, e.g.:

- `get_secret(key="MY_API_KEY", service="file", path="/path/to/.env")`
- `set_secret(key="X", value="y", service="file", path="/path/to/.env")`
- `list_keys(service="file", path="/path/to/.env")`

You can set `ENVELOPER_SERVICE=file` and `ENVELOPER_PATH=/path/to/.env` (if your client supports env) so the LLM doesn’t need to pass them every time.

## Security

The MCP server has **full read/write** access to the configured stores (keychain, file, or cloud). Only run it in a **trusted environment**. Anyone who can start the server (or the process that spawns it) can read and change secrets for the scopes allowed by your config.

## More

- [MCP server docs](../../docs/mcp.md) — Full tool list, parameters, and client setup.
- [LLM guidelines (MCP)](../../LLM/guidelines/mcp.md) — For LLMs helping users set up MCP.
- Sample Cursor config: [cursor-mcp-sample.json](cursor-mcp-sample.json).
