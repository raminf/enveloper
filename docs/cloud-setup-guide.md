# Cloud Setup Guide: Azure, GCP, and AWS

Step-by-step setup for using enveloper with **Azure Key Vault**, **Google Cloud Secret Manager**, and **AWS Systems Manager Parameter Store**. Covers credentials, IAM/RBAC, `.enveloper.toml`, and testing.

---

## Where to put config

- **Config file:** If `~/.enveloper` exists, enveloper loads `~/.enveloper/.enveloper.toml`. Otherwise it searches **upward from the current working directory** for `.enveloper.toml`. See [Project Config](project-config.md) for the full format.
- **Samples:** Copy `sample.enveloper.toml` or `sample.enveloper.minimal.toml` from the repo to `~/.enveloper/.enveloper.toml` or your project root as `.enveloper.toml`.
- **Environment variables:** You can skip the config file and set service-specific env vars (e.g. `ENVELOPER_AZURE_VAULT_URL`, `ENVELOPER_GCP_PROJECT`) instead.

---

## Azure Key Vault

### 1. Install the Azure extra

```bash
pip install enveloper[azure]
# or with uv
uv sync --extra azure
```

### 2. Create a Key Vault

```bash
az login
az keyvault create --name YOUR-VAULT-NAME --resource-group YOUR-RG
```

Use a unique vault name (e.g. `myapp-enveloper-prod`). The vault URL will be `https://YOUR-VAULT-NAME.vault.azure.net/`.

### 3. Credentials (Azure CLI)

enveloper uses **DefaultAzureCredential**, which includes Azure CLI. Log in:

```bash
az login
```

No extra env vars are required for local use. For CI or service principals, set `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, and `AZURE_CLIENT_SECRET`, or use a managed identity.

### 4. Permissions (RBAC)

If the vault was created with **RBAC** (`--enable-rbac-authorization`), do **not** use `az keyvault set-policy`. Assign a role instead.

**Option A: Key Vault Administrator (recommended)**  
Use this if you want to run **`enveloper clear`** (and optionally **`enveloper clear --all`**). Clear permanently removes secrets (purge) so you can push the same names again immediately. The **Key Vault Administrator** role includes `secrets/purge` and all other secret operations.

```bash
az role assignment create \
  --role "Key Vault Administrator" \
  --assignee $(az ad signed-in-user show --query id -o tsv) \
  --scope $(az keyvault show -n YOUR-VAULT-NAME -g YOUR-RG --query id -o tsv)
```

**Option B: Key Vault Secrets Officer**  
Enough for push/pull and list. Does **not** include purge; if you run `enveloper clear`, secrets are soft-deleted only and you may get conflicts reusing the same names until they are purged or recovered.

```bash
az role assignment create \
  --role "Key Vault Secrets Officer" \
  --assignee $(az ad signed-in-user show --query id -o tsv) \
  --scope $(az keyvault show -n YOUR-VAULT-NAME -g YOUR-RG --query id -o tsv)
```

For read-only (list/get only), use **Key Vault Secrets User**. Wait 1–2 minutes for RBAC to propagate.

### 5. Config

**.enveloper.toml:**

```toml
[enveloper]
project = "myapp"
service = "local"

[enveloper.azure]
vault_url = "https://YOUR-VAULT-NAME.vault.azure.net/"
```

Or use the env var (no config file):

```bash
export ENVELOPER_AZURE_VAULT_URL="https://YOUR-VAULT-NAME.vault.azure.net/"
# or just the vault name:
export ENVELOPER_AZURE_VAULT_URL="YOUR-VAULT-NAME"
```

### 6. Test

```bash
# List (empty at first)
enveloper list keys --domain dev --project myapp --service azure

# Push from local keychain to Azure
enveloper push --domain dev --project myapp --service azure

# List again to verify
enveloper list keys --domain dev --project myapp --service azure
```

---

## Google Cloud Secret Manager

### 1. Install the GCP extra

```bash
pip install enveloper[gcp]
# or with uv
uv sync --extra gcp
```

### 2. Create / select a GCP project

Use an existing project or create one in the [Google Cloud Console](https://console.cloud.google.com/). Note the **project ID** (e.g. `my-app-123456`), not the display name.

### 3. Enable Secret Manager API

```bash
gcloud services enable secretmanager.googleapis.com --project=YOUR-PROJECT-ID
```

### 4. Credentials

enveloper uses **Application Default Credentials**. For local use:

```bash
gcloud auth application-default login
gcloud config set project YOUR-PROJECT-ID
```

For CI, use a service account key or Workload Identity.

### 5. Permissions

Your user or service account needs **Secret Manager Admin** (or at least **Secret Manager Secret Accessor** for read and **Secret Manager Admin** for write):

- In Console: IAM & Admin → IAM → Add principal → role “Secret Manager Admin”.
- Or with gcloud (replace `YOUR-EMAIL` and `YOUR-PROJECT-ID`):

```bash
gcloud projects add-iam-policy-binding YOUR-PROJECT-ID \
  --member="user:YOUR-EMAIL" \
  --role="roles/secretmanager.admin"
```

### 6. Config

**.enveloper.toml:**

```toml
[enveloper]
project = "myapp"
service = "local"

[enveloper.gcp]
project = "YOUR-PROJECT-ID"
```

You can use the **project ID** or the **Project name** (display name); enveloper resolves the display name to the project ID. Or set an env var:

```bash
export ENVELOPER_GCP_PROJECT="YOUR-PROJECT-ID"
# or
export GOOGLE_CLOUD_PROJECT="YOUR-PROJECT-ID"
```

If unset, enveloper uses `gcloud config get-value project`.

### 7. Test

```bash
enveloper list keys --domain dev --project myapp --service gcp
enveloper push --domain dev --project myapp --service gcp
enveloper list keys --domain dev --project myapp --service gcp
```

---

## AWS Systems Manager Parameter Store

### 1. Install the AWS extra

```bash
pip install enveloper[aws]
# or with uv
uv sync --extra aws
```

### 2. Credentials

Use the AWS CLI or env vars:

```bash
aws configure
# or
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export AWS_DEFAULT_REGION=us-east-1
```

### 3. Permissions

The IAM user or role needs at least:

- `ssm:GetParameter`, `ssm:GetParameters`
- `ssm:PutParameter`
- `ssm:DeleteParameter`
- `ssm:GetParametersByPath` (for list)

Example minimal policy (restrict `Resource` as needed):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ssm:GetParameter",
        "ssm:GetParameters",
        "ssm:PutParameter",
        "ssm:DeleteParameter",
        "ssm:GetParametersByPath"
      ],
      "Resource": "*"
    }
  ]
}
```

For encrypted parameters, add `kms:Decrypt` (and optionally `kms:Encrypt`) on the KMS key used by SSM.

### 4. Config

**.enveloper.toml:**

```toml
[enveloper]
project = "myapp"
service = "local"

[enveloper.aws]
profile = "default"
region = "us-east-1"
```

Omit `profile`/`region` to use `AWS_PROFILE` and `AWS_DEFAULT_REGION`.

### 5. Test

```bash
enveloper list keys --domain dev --project myapp --service aws
enveloper push --domain dev --project myapp --service aws
enveloper list keys --domain dev --project myapp --service aws
```

---

## HashiCorp Vault (local Docker or server)

The **`vault`** store works with **any** Vault that exposes the KV v2 API: local Vault in Docker (for development/testing) or a real deployment (self-hosted or HCP Vault Dedicated). You use the same `--service vault` and config; only `VAULT_ADDR` and `VAULT_TOKEN` change.

### Option A: Local Vault in Docker (no cloud, good for tests)

No cloud account. Run Vault in dev mode locally:

**1. Start Vault**

From the repo (or wherever you put the compose file):

```bash
docker compose -f docker-compose.vault.yml up -d
```

The Vault **web UI** is available at **http://127.0.0.1:8200/ui** — sign in with token `root`.

**2. KV v2 at `secret/`**

Recent Vault dev servers (1.15+) mount KV v2 at `secret/` by default, so nothing else is needed. If you use an older image and get errors about versioning, enable KV v2 once:

```bash
docker compose -f docker-compose.vault.yml exec vault vault secrets disable secret
docker compose -f docker-compose.vault.yml exec vault vault secrets enable -path=secret kv-v2
```

**3. Set env vars and config**

```bash
export VAULT_ADDR=http://127.0.0.1:8200
export VAULT_TOKEN=root
```

Or in `.enveloper.toml`:

```toml
[enveloper.vault]
url = "http://127.0.0.1:8200"
mount = "secret"
```

The token must be set via **`VAULT_TOKEN`** (or your shell); avoid putting the root token in the config file.

**4. Install vault extra and test**

```bash
pip install enveloper[vault]
# or: uv sync --extra vault
enveloper list keys --domain dev --project myapp --service vault
enveloper push --domain dev --project myapp --service vault
```

**Stop:** `docker compose -f docker-compose.vault.yml down`

### Option B: Real Vault (self-hosted or HCP Vault Dedicated)

Use your server or HCP Vault Dedicated URL and a token with read/write on the KV v2 mount:

- **VAULT_ADDR** – e.g. `https://vault.example.com` or your HCP cluster address  
- **VAULT_TOKEN** – token with policy allowing `secret/*` (or the mount you use)  
- **Config:** `[enveloper.vault]` with `url` and `mount` as needed  

Same `enveloper push --service vault` / `pull --service vault`; only the address and token differ.

---

## Quick reference

| Cloud  | Config / env | Credentials | Docs |
|--------|----------------|-------------|------|
| **Azure** | `[enveloper.azure]` `vault_url` or `ENVELOPER_AZURE_VAULT_URL` | `az login` or service principal | [Azure Key Vault](https://learn.microsoft.com/en-us/azure/key-vault/) |
| **GCP**  | `[enveloper.gcp]` `project` or `ENVELOPER_GCP_PROJECT` / `GOOGLE_CLOUD_PROJECT` | `gcloud auth application-default login` | [Secret Manager](https://cloud.google.com/secret-manager/docs) |
| **AWS**  | `[enveloper.aws]` `profile`, `region` or `AWS_PROFILE`, `AWS_DEFAULT_REGION` | `aws configure` or env vars | [Parameter Store](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html) |
| **Vault** (local or server) | `[enveloper.vault]` `url`, `mount` or `VAULT_ADDR`, `VAULT_TOKEN` | Root or policy token (local dev: `root`) | [Vault KV v2](https://developer.hashicorp.com/vault/docs/secrets/kv/kv-v2) |

For Aliyun and GitHub, see [Cloud Storage](cloud-storage.md) and [Project Config](project-config.md).
