# Loading values into GitHub Actions secrets

This example shows how to **push** secrets from your local keychain (or another source) into **GitHub Actions repository secrets** using `enveloper push --service github`. No `.env` file is committed; values are sent via the `gh` CLI so they appear as encrypted secrets in your repo (e.g. `secrets.MY_API_KEY` in workflows).

## Prerequisites

- [GitHub CLI (`gh`)](https://cli.github.com/) installed and authenticated: `gh auth login`
- Enveloper installed: `pip install enveloper` (the GitHub store uses `gh`; no extra deps)

## Workflow

1. **Import** variables into the local keychain (one-time or after changing values):

   ```bash
   enveloper import sample.env --domain mydomain --project myproject
   ```

   Or use any domain/project you prefer; the same scope is used when pushing.

2. **Push** from the keychain to GitHub repository secrets:

   ```bash
   enveloper push --service github --repo OWNER/REPO --domain mydomain --project myproject
   ```

   Replace `OWNER/REPO` with your GitHub repository (e.g. `myorg/myapp` or use `${{ github.repository }}` in a workflow). If you are already in the repo, you can omit `--repo` and `gh` will use the current repository.

3. In your **GitHub Actions workflow**, use the secrets as usual. They are available as `${{ secrets.MY_API_KEY }}`, `${{ secrets.LEVEL_SET }}`, etc. (the key names from your env set).

## Integration with sample.env

Using the [sample.env](../sample.env) from this repo:

```bash
# From the repo root or examples/
enveloper import sample.env -d mydomain -p myproject
enveloper push --service github -d mydomain -p myproject --repo owner/repo
```

Then in a workflow:

```yaml
env:
  MY_API_KEY: ${{ secrets.MY_API_KEY }}
  LEVEL_SET: ${{ secrets.LEVEL_SET }}
```

Or inject into a step:

```yaml
- run: ./script.sh
  env:
    MY_API_KEY: ${{ secrets.MY_API_KEY }}
    MY_API_SECRET: ${{ secrets.MY_API_SECRET }}
```

## Notes

- **GitHub Secrets are write-only**: you can list secret *names* with `gh secret list`, but values cannot be read back. Pushing overwrites any existing secret with the same name.
- **Key names**: Enveloper sends the same variable names you have in the keychain (e.g. `MY_API_KEY`, `LEVEL_SET`). Those become the GitHub secret names.
- **Export / unexport**: This example is about *loading values into* GitHub Secrets (push). To *use* those secrets in a runner, your workflow already has access via `secrets.*`. If you run the CLI inside the runner (e.g. to pull from AWS and then export), use `eval "$(enveloper export ...)"` as in the [CI/CD example](../cicd/).

## Files in this folder

| File | Purpose |
|------|--------|
| [push-to-github.sh](push-to-github.sh) | Example script: import from sample.env, then push to GitHub (set REPO before running). |
