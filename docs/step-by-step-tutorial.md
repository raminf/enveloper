# Step-by-Step Tutorial

This tutorial walks you through enveloper from a simple local `.env` file to keychain storage, desktop builds, and AWS SSM. You can follow along on macOS, Linux, or Windows.

---

## 1. Create a sample .env file

Create a file named `sample.env` in your project directory with some example variables:

```bash
# sample.env
TWILIO_API_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN="my secret token"
MESSAGING_PROVIDER=twilio

# Quoted and special values
SINGLE_QUOTED='hello world'
EQUALS_IN_VALUE=postgres://user:pass@host/db?opt=1
```

*(Screenshots: terminal showing the file can be added here.)*

---

## 2. Install the CLI

Install enveloper with pip (or poetry/uv):

```bash
pip install enveloper
```

Verify:

```bash
enveloper --version
```

---

## 3. Import into keychain

Import the contents of `sample.env` into your OS keychain. Use a **domain** to scope the secrets (e.g. `tutorial` or `prod`):

```bash
enveloper import sample.env --domain tutorial
```

You should see: `Imported N variable(s) from sample.env`.

*(Screenshots: Mac Keychain Access or equivalent showing stored entries can be added here.)*

---

## 4. List the values

List all secrets stored for that domain:

```bash
enveloper list --domain tutorial
```

The table shows key names and masked values.

---

## 5. Get a single value

Retrieve one secret by name:

```bash
enveloper get TWILIO_API_SID --domain tutorial
```

The value is printed to stdout.

---

## 6. Modify a single value (then verify)

Set a key to a new value:

```bash
enveloper set TWILIO_AUTH_TOKEN "updated secret token" --domain tutorial
```

Verify:

```bash
enveloper get TWILIO_AUTH_TOKEN --domain tutorial
```

You should see `updated secret token`.

---

## 7. Delete a single value (then verify it's gone)

Remove one key:

```bash
enveloper delete MESSAGING_PROVIDER --domain tutorial
```

Verify it is gone:

```bash
enveloper get MESSAGING_PROVIDER --domain tutorial
```

You should see an error that the key was not found, and it will no longer appear in `enveloper list --domain tutorial`.

---

## 8. Clear all entries, then verify

Remove every secret for the current domain:

```bash
enveloper clear --domain tutorial
```

Confirm when prompted (or use `--quiet` / `-q` to skip confirmation).

Verify:

```bash
enveloper list --domain tutorial
```

The list should be empty (or show no secrets).

---

## 9. Re-import, modify, add one manually, export to file

Re-import from `sample.env`:

```bash
enveloper import sample.env --domain tutorial
```

Modify one value:

```bash
enveloper set TWILIO_AUTH_TOKEN "modified in keychain" --domain tutorial
```

Add a new key manually:

```bash
enveloper set EXTRA_KEY "added by hand" --domain tutorial
```

Export everything to a new file:

```bash
enveloper export --domain tutorial --output newsample.env
```

List the contents of the file to verify:

```bash
cat newsample.env
```

You should see the updated and new values (e.g. `TWILIO_AUTH_TOKEN=modified in keychain`, `EXTRA_KEY=added by hand`).

---

## 10. Using it as part of a desktop build (Makefile)

Load secrets into the environment before a build and unset them after.

**Export for the build:**

```makefile
# Load secrets into the shell for this make run
export ENVELOPER_DOMAIN := tutorial
include .env.export

.env.export:
	@enveloper export -d tutorial --format dotenv > .env.export

build: .env.export
	@echo "Building with secrets in environment..."
	@env | grep -E '^(TWILIO_|MESSAGING_)' || true

clean:
	rm -f .env.export
```

Or use the **eval** pattern so variables are set only for the commands that need them:

```makefile
DOMAIN ?= tutorial

build:
	eval "$$(enveloper export -d $(DOMAIN) --format unix)" && \
		$(MAKE) do-build

do-build:
	@echo "TWILIO_API_SID is set: $$(echo $${TWILIO_API_SID:0:10})..."
```

---

## 11. Export, build, then unexport to clear env

In a shell (or Makefile target):

```bash
# Load secrets into current shell
eval "$(enveloper export -d tutorial --format unix)"

# Run your build
make build

# Remove those variables from the shell
eval "$(enveloper unexport -d tutorial)"
```

After `unexport`, the variables that were set by `export` are unset.

---

## 12. Use on Windows PowerShell

Import and list work the same; use `--format win` for PowerShell-compatible export/unexport.

**Import and list:**

```powershell
enveloper import sample.env --domain tutorial
enveloper list --domain tutorial
```

**Export into the current session:**

```powershell
enveloper export -d tutorial --format win | Invoke-Expression
```

**Unexport (remove the variables):**

```powershell
enveloper unexport -d tutorial --format win | Invoke-Expression
```

---

## 13. Set up AWS default profile and import from sample.env

Install the AWS extra and configure credentials:

```bash
pip install enveloper[aws]
```

Ensure you have an AWS profile (e.g. `default`) or set `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`. Optionally set region:

```bash
export AWS_DEFAULT_REGION=us-west-2
# or use --region with commands
```

Import from `sample.env` into the local keychain, then push to AWS so we can list from AWS in the next step:

```bash
enveloper import sample.env --domain tutorial
enveloper --service aws push --from local --domain tutorial
```

---

## 14. List from AWS

To read from AWS SSM, use `--service aws` and the same project/domain (and optional prefix). First push to AWS (see below), then:

```bash
enveloper --service aws --domain tutorial list
```

You’ll see the same key names with masked values, as stored in SSM.

*(Screenshot: AWS Console → Systems Manager → Parameter Store, showing the parameters under the prefix used by enveloper (e.g. `/envr/...`) can be added here.)*

---

## 15. AWS Console: where secrets live in SSM

Secrets are stored under a path that includes the default prefix, domain, project, and version, for example:

`/envr/tutorial/<project>/1.0.0/<KEY_NAME>`

In the AWS Console, open **Systems Manager** → **Parameter Store** and look under the prefix you configured (or the default). Each key from your `.env` appears as a parameter.

*(Screenshot placeholder: AWS SSM Parameter Store console showing the enveloper parameters.)*

---

## 16. Same Makefile import but from AWS SSM

Use the AWS store as the source of truth for the build:

```makefile
DOMAIN := tutorial

# Load from AWS SSM instead of keychain
build:
	eval "$$(enveloper -s aws export -d $(DOMAIN) --format unix)" && \
		$(MAKE) do-build
	eval "$$(enveloper -s aws unexport -d $(DOMAIN))"

do-build:
	@echo "Building with AWS-backed secrets..."
```

Or with explicit service:

```makefile
build:
	enveloper --service aws --domain $(DOMAIN) export --format unix > .env.aws
	$(MAKE) do-build
	rm -f .env.aws
```

---

## 17. Clear the settings in AWS

Remove all secrets for that domain/project from AWS SSM:

```bash
enveloper --service aws --domain tutorial clear --quiet
```

Confirm when prompted unless you use `--quiet`. Then list again to verify:

```bash
enveloper --service aws --domain tutorial list
```

---

## 18. Import into keychain, then push to AWS

Import from `sample.env` into the **local keychain**:

```bash
enveloper import sample.env --domain tutorial
```

Push those secrets to AWS SSM:

```bash
enveloper --service aws push --from local --domain tutorial
```

Secrets are now in both the keychain and AWS.

---

## 19. List both keychain and SSM

**Keychain (default service):**

```bash
enveloper list --domain tutorial
```

**AWS SSM:**

```bash
enveloper --service aws list --domain tutorial
```

Both should show the same set of key names (with possibly different masked values if you changed one store).

---

## 20. Clear the local keychain only

Remove all secrets for the domain from the keychain, leaving AWS unchanged:

```bash
enveloper clear --domain tutorial --quiet
```

List keychain again: empty. List AWS again: still has the keys.

---

## 21. Override service with environment variables

You can point enveloper at a service (or domain/project) via environment variables so you don’t need to pass flags every time:

```bash
export ENVELOPER_SERVICE=aws
export ENVELOPER_DOMAIN=tutorial
export ENVELOPER_PROJECT=myapp

enveloper list
enveloper get TWILIO_API_SID
```

The CLI uses these when you omit `--service` and `--domain`/`--project`.

---

## 22. Domains and projects

- **Domain** – A scope (e.g. `prod`, `staging`, `tutorial`). Use `--domain` or `ENVELOPER_DOMAIN`.
- **Project** – A namespace (e.g. `myapp`, `backend`). Use `--project` or `ENVELOPER_PROJECT`.

Together they form the path/prefix under which keys are stored. Examples:

```bash
# Different domains for different environments
enveloper import sample.env --domain prod
enveloper import sample.env --domain staging

# Different projects in the same domain
enveloper import sample.env --domain prod --project api
enveloper import sample.env --domain prod --project worker

# List per domain (and optionally project)
enveloper list --domain prod
enveloper list --domain prod --project api
```

---

## 23. Export to YAML and JSON

Export the current set of secrets to structured files:

**YAML:**

```bash
enveloper export --domain tutorial --format yaml --output secrets.yaml
cat secrets.yaml
```

**JSON:**

```bash
enveloper export --domain tutorial --format json --output secrets.json
cat secrets.json
```

You can re-import later with `--format yaml` or `--format json`:

```bash
enveloper import secrets.yaml --format yaml --domain backup
enveloper import secrets.json --format json --domain backup
```

---

## 24. Versions: multiple versions of the same set

Enveloper supports **versioned** secrets (semver, e.g. `1.0.0`, `2.0.0`). Import the same file into two versions:

```bash
enveloper import sample.env --domain tutorial --version 1.0.0
enveloper import sample.env --domain tutorial --version 2.0.0
```

Modify one value only in version `2.0.0`:

```bash
enveloper set TWILIO_AUTH_TOKEN "only in 2.0.0" --domain tutorial --version 2.0.0
```

List values for each version:

```bash
enveloper list --domain tutorial --version 1.0.0
enveloper list --domain tutorial --version 2.0.0
```

In `1.0.0`, `TWILIO_AUTH_TOKEN` is unchanged from the import. In `2.0.0`, it shows the updated value.

---

## 25. Dotenv-compatible SDK (services, domains, projects, versions)

Enveloper provides a Python API compatible with `python-dotenv` (`load_dotenv` and `dotenv_values`), with support for **service**, **domain**, **project**, and **version**:

```python
from enveloper import load_dotenv, dotenv_values

# Load from keychain (default)
load_dotenv(project="myapp", domain="tutorial")

# Load from a specific version
load_dotenv(project="myapp", domain="tutorial", version="2.0.0")

# Get dict from AWS without touching os.environ
env = dotenv_values(service="aws", project="myapp", domain="prod", version="1.0.0")
```

See the [SDK](sdk.md) documentation for full details and examples.

---

## Screenshot placeholders

*(The following placeholders can be replaced with real screenshots when available.)*

- **Mac Keychain:** Keychain Access (or equivalent) showing enveloper-stored entries.
- **AWS Console:** Systems Manager → Parameter Store with the enveloper prefix and parameters.
- **Terminal:** Sample output of `enveloper list`, `enveloper export`, and a Makefile run.
- **Windows:** PowerShell session showing `enveloper export --format win | Invoke-Expression` and `unexport`.
