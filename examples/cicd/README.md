# Using enveloper in CI/CD

This example shows how to use **enveloper** in a CI/CD pipeline (e.g. GitHub Actions) so that secrets are **imported** into the keychain or pulled from a cloud store, then **exported** (unix format) into the job environment, and optionally **unexported** at the end. No `.env` file is committed or written to the runner disk (except temporarily if you choose to).

## Concepts

- **import**: Load variables from a file into the store (e.g. one-time setup, or from a secret that contains env content).
- **export --format unix**: Emit `export VAR=value` lines; use with `eval` to load into the shell.
- **unexport**: Emit `unset VAR` lines; use with `eval` to clear those variables from the shell.

## Integration with sample.env

1. Store the contents of [sample.env](../sample.env) (or real secrets) in your CI secret store (e.g. GitHub Actions secrets, or AWS SSM). For GitHub, you might have a secret `ENV_FILE` containing the file body.

2. In the job:
   - **Option A**: Pull from cloud: `enveloper pull --service aws` (with AWS credentials from CI secrets), then `eval "$(enveloper export --format unix)"`.
   - **Option B**: Import from a secret that holds the file: echo the secret into a file, then `enveloper import that.env`, then `eval "$(enveloper export --format unix)"`.

3. Run your build/test/deploy steps; they see the variables in the environment.

4. At the end of the job (optional): `eval "$(enveloper unexport --format unix)"` to clear the variables from the shell.

## Files in this folder

| File | Purpose |
|------|--------|
| [github-actions.yml](github-actions.yml) | Example GitHub Actions workflow: install enveloper, pull (or import), export, run steps, unexport. |

## GitHub Actions example

The workflow:

1. Checks out the repo and sets up Python.
2. Installs `enveloper[aws]`.
3. Pulls secrets from AWS SSM (using `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` from GitHub secrets), or imports from a secret file.
4. Runs `eval "$(enveloper export -d mydomain -p myproject --format unix)"` so subsequent steps see the env.
5. Runs a demo step (e.g. print that vars are set).
6. Optionally runs `eval "$(enveloper unexport ...)"` in a final step.

No `.env` file is committed; secrets live in GitHub Secrets and/or AWS.

## Run the example workflow

- Add repository secrets: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` (and optionally `ENV_FILE` if using import-from-secret).
- Ensure AWS SSM has the parameters for the chosen domain/project/prefix (if using pull).
- Push to a branch that triggers the workflow, or run it manually.
