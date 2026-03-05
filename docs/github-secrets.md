# Loading values into GitHub Actions secrets

You can push secrets from your local keychain (or from a file) into **GitHub Actions repository secrets** using `enveloper push --service github`. Values are sent via the GitHub CLI (`gh secret set`); no `.env` file is committed.

## Prerequisites

- [GitHub CLI (`gh`)](https://cli.github.com/) installed and authenticated: `gh auth login`
- Enveloper installed: `pip install enveloper` (no extra deps for the GitHub store)

## Workflow

1. **Import** variables into the local keychain (e.g. from a `.env` file):

   ```bash
   enveloper import sample.env --domain mydomain --project myproject
   ```

2. **Push** to GitHub repository secrets:

   ```bash
   enveloper push --service github --repo OWNER/REPO --domain mydomain --project myproject
   ```

   Omit `--repo` to use the current repository (when run inside a git repo with `gh` configured).

3. In your **GitHub Actions workflow**, use the secrets as `${{ secrets.MY_API_KEY }}`, `${{ secrets.LEVEL_SET }}`, etc.

## Notes

- **GitHub Secrets are write-only**: you can list names with `gh secret list`, but values cannot be read back.
- Key names in the keychain become the GitHub secret names (e.g. `MY_API_KEY`, `LEVEL_SET`).

See the [GitHub secrets example](../examples/github-secrets/README.md) for a runnable script and more detail.
