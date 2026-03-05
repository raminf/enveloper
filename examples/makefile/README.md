# Using enveloper in a Makefile

This example shows how to load secrets from enveloper (keychain or cloud) into the Make environment using **import**, **export** (unix format), and **unexport**, without committing a `.env` file.

## Integration with sample.env

1. **One-time**: Import the example set into the keychain (or push to AWS and pull when needed):

   ```bash
   enveloper import sample.env --domain mydomain --project myproject
   ```

2. In the Makefile we **export** so variables are available to targets, and optionally **unexport** in a cleanup target.

## How it works

- **Load secrets**: A dependency target or include runs `enveloper export -d mydomain -p myproject --format unix` and the Makefile sources that output so `MY_API_KEY`, `LEVEL_SET`, etc. are set for all targets.
- **Use in targets**: Any target can rely on `$(MY_API_KEY)` or run a shell that has those variables.
- **Cleanup**: A target can run `eval "$(enveloper unexport --format unix)"` in a shell to clear the variables from that shell (e.g. in a `clean` or `unexport` target).

See [Makefile](Makefile) for a full example.

## Files in this folder

| File | Purpose |
|------|--------|
| [Makefile](Makefile) | Loads env via enveloper export, runs a demo target, optional unexport. |

## Run

From the **repository root** (so that `enveloper` is on PATH, or ensure `enveloper` is installed and on PATH):

```bash
# Load from keychain and run the demo target
make -f examples/makefile/Makefile demo

# Optional: unexport in the same shell (run in subshell or source the Makefile)
make -f examples/makefile/Makefile unexport
```

The Makefile uses `eval "$$(enveloper ... export --format unix)"` in a target so that the variables are available to commands in that target. For variables to be available to all targets, the example uses a generated env file or an `include` pattern as in the main [Makefile Integration](../../docs/makefile-integration.md) docs.
