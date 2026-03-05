# Using enveloper in a shell script

This example shows how to use **enveloper** in a plain shell script: **import** (or pull) to load the keychain, **export --format unix** to load variables into the environment, run your app, then **unexport** to clear them. No `.env` file is required in the repo or on disk at runtime.

## Integration with sample.env

1. **One-time**: Import the example set into the keychain (or push to AWS and pull when needed):

   ```bash
   enveloper import sample.env --domain mydomain --project myproject
   ```

2. In the script:
   - `eval "$(enveloper --domain mydomain --project myproject export --format unix)"` — loads `MY_API_KEY`, `MY_API_SECRET`, `LEVEL_SET` into the current shell.
   - Run your application or commands; they see the variables.
   - `eval "$(enveloper --domain mydomain --project myproject unexport --format unix)"` — clears those variables from the shell.

## Files in this folder

| File | Purpose |
|------|--------|
| [run_with_secrets.sh](run_with_secrets.sh) | Example script: export, run a demo command, unexport. |

## Run

From the repository root (with `enveloper` on PATH):

```bash
./examples/shell/run_with_secrets.sh
```

Or with domain/project overrides:

```bash
ENVELOPER_DOMAIN=dev ENVELOPER_PROJECT=myapp ./examples/shell/run_with_secrets.sh
```

The script uses `export` to load env and `unexport` to clear it in the same process, so secrets are only in memory for the duration of the script.
