# Step-by-step: MCP with enveloper

Follow these steps to let an LLM agent (e.g. in Cursor) access your environment variables from enveloper (local keychain or cloud).

## 1. Install enveloper with MCP support

```bash
pip install enveloper[mcp]
```

Or with uv:

```bash
uv pip install enveloper[mcp]
```

Verify:

```bash
enveloper-mcp --help
# or
uv run python -c "from enveloper.mcp_server import list_services; print(list_services())"
```

## 2. Add secrets (choose one)

**A. Local keychain (default)**

```bash
# From the examples folder
enveloper import sample.env --domain mydomain --project myproject
```

**B. Use a .env file**

Create a file (e.g. `my.env`) with:

```
MY_API_KEY=abc123
MY_API_SECRET=xyz
```

The LLM will use `service="file"` and `path="/full/path/to/my.env"` when calling tools.

## 3. Configure your MCP client

### Cursor

1. Open **Settings** (or **Cursor Settings**).
2. Go to **MCP** (or **Features → MCP**).
3. Add a new server. Example:

| Field   | Value |
|--------|--------|
| Name   | `enveloper` |
| Command | `enveloper-mcp` |
| Args   | (empty) |

If `enveloper-mcp` is not on your PATH, use:

| Field   | Value |
|--------|--------|
| Command | `uv` |
| Args   | `run`, `python`, `-m`, `enveloper.mcp_server` |
| Cwd    | Path to the folder that contains the enveloper package (e.g. your project or `enveloper-py`) |

4. Save and restart Cursor if needed.

### Claude Desktop / other clients

Set the server command to `enveloper-mcp` (or `uv run python -m enveloper.mcp_server`) with **stdio** transport. See your client’s docs for adding an MCP server.

## 4. Use from the LLM

Once the server is connected, the LLM can **get a secret**, **list keys**, **set a secret**, **export env**, and so on. Tool names use underscores in code (e.g. `get_secret`); messages are human-friendly (e.g. "Secret not found"). Examples:

- **List services (available backends):**  
  `list_services()`

- **List keys (keychain, mydomain / myproject):**  
  `list_keys(domain="mydomain", project="myproject")`

- **Get a secret:**  
  `get_secret(key="MY_API_KEY", domain="mydomain", project="myproject")`

- **Get a secret from a .env file:**  
  `get_secret(key="MY_API_KEY", service="file", path="/path/to/my.env")`

- **Export env (all as shell commands):**  
  `export_env(domain="mydomain", project="myproject", format="unix")`

- **Set a secret:**  
  `set_secret(key="NEW_KEY", value="secret", domain="mydomain", project="myproject")`

- **Import from file:**  
  `import_from_file(file_path="/path/to/my.env", domain="mydomain", project="myproject")`

Defaults: `domain` and `project` (and `version`, `service`) come from env vars **ENVELOPER_DOMAIN**, **ENVELOPER_PROJECT**, etc., or from **.enveloper.toml**.

## 5. Cloud stores (optional)

To use AWS, GCP, GitHub, etc.:

1. Install the right extra, e.g. `pip install enveloper[mcp,aws]`.
2. Configure credentials (env vars, config file, or default chain) as per [Cloud Setup Guide](../../docs/cloud-setup-guide.md).
3. Call tools with `service="aws"` (or the store name), or set **ENVELOPER_SERVICE**.
4. **Push to service** and **pull from service** push from keychain to cloud or pull from cloud to keychain.

## Troubleshooting

- **“command not found: enveloper-mcp”**  
  Use the `uv` variant with `cwd` set to the project root, or ensure the env that has `enveloper[mcp]` installed is on PATH when the client runs the command.

- **“secret not found”**  
  Check `domain` and `project` (and `service`, `path` for file). Use **list keys** or **list domains** / **list projects** to see what’s there.

- **Server doesn’t start**  
  Run `enveloper-mcp` in a terminal to see errors. Ensure `pip install enveloper[mcp]` completed and no firewall is blocking stdio.
