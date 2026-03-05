# Loading secrets in Python with the SDK

This example shows how to load secrets into a **Python script** using the enveloper SDK (`load_dotenv` and `dotenv_values`). No `.env` file is required at runtime; values come from the system keychain or a cloud store (e.g. AWS SSM).

## Prerequisites

Install enveloper with the **SDK** extra (required for `load_dotenv` and `dotenv_values`):

```bash
pip install enveloper[sdk]
```

For a specific cloud backend (e.g. AWS):

```bash
pip install enveloper[sdk,aws]
```

## Concepts

- **`load_dotenv()`** — Loads secrets into `os.environ` so the rest of your script (and subprocesses) see them. Compatible with the `python-dotenv` API.
- **`dotenv_values()`** — Returns a dictionary of secrets without modifying the process environment. Use when you want to pass config to a function or avoid touching `os.environ`.

Domain and project (and optional `service`, `version`) scope which secrets are loaded, same as the CLI.

## Integration with sample.env

1. **Import** the example set into the keychain (one-time):

   ```bash
   enveloper import sample.env --domain mydomain --project myproject
   ```

2. In your Python script, load with the same domain/project:

   ```python
   from enveloper import load_dotenv

   load_dotenv(domain="mydomain", project="myproject")
   # Now os.environ["MY_API_KEY"], os.environ["LEVEL_SET"], etc. are set
   ```

   Or use `dotenv_values()` to get a dict without changing the environment:

   ```python
   from enveloper import dotenv_values

   secrets = dotenv_values(domain="mydomain", project="myproject")
   api_key = secrets.get("MY_API_KEY")
   ```

## Files in this folder

| File | Purpose |
|------|--------|
| [app.py](app.py) | Sample script: uses `load_dotenv` and `dotenv_values` to load from keychain (or file) and run a minimal “app”. |

## Run the example

From the repository root (with enveloper and the keychain populated):

```bash
# Optional: ensure keychain has the sample set
enveloper import examples/sample.env -d mydomain -p myproject

# Run the sample app (loads from keychain by default)
uv run python examples/sdk/app.py
```

Or load from a `.env` file (no keychain needed):

```bash
ENVELOPER_SERVICE=file ENVELOPER_DOMAIN=mydomain ENVELOPER_PROJECT=myproject \
  uv run python examples/sdk/app.py
```

(with a `.env` in the current directory containing `MY_API_KEY`, `LEVEL_SET`, etc.)

## Configuration

You can pass options explicitly or use environment variables (same as the CLI):

| Env var | Purpose |
|--------|---------|
| `ENVELOPER_DOMAIN` | Domain (e.g. `mydomain`) |
| `ENVELOPER_PROJECT` | Project (e.g. `myproject`) |
| `ENVELOPER_SERVICE` | Backend: `local`, `file`, `aws`, etc. |
| `ENVELOPER_VERSION` | Version for versioned secrets (default `1.0.0`) |

So `load_dotenv()` with no arguments uses these env vars or your `.enveloper.toml` config.
