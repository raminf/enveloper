# Cloud Storage Details

## Overview

`enveloper` supports multiple cloud secret management services. Each service provides secure storage with team collaboration, backup, and access control features.

## Supported Cloud Services

| Service | Store Name | Install Extra | Read/Write |
|---------|------------|---------------|------------|
| AWS Systems Manager Parameter Store | `aws` | `enveloper[aws]` | Push/Pull |
| GitHub Actions Secrets | `github` | Built-in | Push only |
| HashiCorp Vault KV v2 | `vault` | `enveloper[vault]` | Push/Pull |
| Google Cloud Secret Manager | `gcp` | `enveloper[gcp]` | Push/Pull |
| Azure Key Vault | `azure` | `enveloper[azure]` | Push/Pull |
| Alibaba Cloud KMS Secrets Manager | `aliyun` | `enveloper[alibaba]` | Push/Pull |

## Benefits of Cloud Storage

### Teamwork
- **Shared access:** Multiple team members can access the same secrets
- **Centralized management:** One source of truth for all environments
- **Audit trails:** Track who accessed or modified secrets
- **Role-based access:** Fine-grain permissions per user/team

### Per-Project vs. Global Settings
- **Per-project:** Store secrets under project-specific prefixes
- **Global:** Use shared prefixes for common secrets across projects
- **Environment separation:** Use domain names (dev, staging, prod)

### Persistent Backup
- **Automatic backups:** Cloud providers handle data durability
- **Version history:** Maintain multiple versions of secrets
- **Disaster recovery:** Cross-region replication available
- **No data loss:** Enterprise-grade durability guarantees

### Fine-Grain Access Control
- **IAM policies:** Control who can read/write secrets
- **Resource tags:** Organize and filter by tags
- **Audit logging:** Track all access and modifications
- **Secret rotation:** Built-in rotation policies

## Service-Specific Details

### AWS Systems Manager Parameter Store

**Benefits:**
- Integrated with AWS IAM for access control
- Tiered pricing (Free Tier available)
- Parameter hierarchies for organization
- Encryption with AWS KMS

**Configuration:**
```toml
[enveloper.aws]
profile = "default"  # or set AWS_PROFILE
region = "us-west-2"  # or set AWS_DEFAULT_REGION
```

**Usage:**
```bash
# Push to SSM
enveloper push --service aws -d prod --prefix /myapp/prod/

# Pull from SSM
enveloper pull --service aws -d prod --prefix /myapp/prod/

# In Lambda, use SSM prefix
export ENVELOPER_SSM_PREFIX=/myapp/prod/
```

### GitHub Actions Secrets

**Benefits:**
- Native integration with GitHub Actions
- No additional cost
- Repository-level or organization-level secrets
- Environment-specific secrets

**Usage:**
```bash
# Push to GitHub Actions
enveloper push --service github -d prod --repo owner/repo

# In workflow, use secrets directly
- name: Use secret
  run: echo "${{ secrets.MY_KEY }}"
```

**Limitations:**
- Write-only (cannot pull from GitHub)
- Repository-scoped (not domain/project aware)

### HashiCorp Vault KV v2

**Benefits:**
- Advanced secret management features
- Dynamic secrets generation
- Lease management and revocation
- Multiple secret backends

**Configuration:**
```toml
[enveloper.vault]
url = "http://127.0.0.1:8200"  # or set VAULT_ADDR
mount = "secret"  # KV v2 mount point (default "secret")
```

**Authentication:**
- `VAULT_TOKEN` - Token authentication
- `VAULT_ADDR` - Vault server address

**Usage:**
```bash
# Push to Vault
enveloper push --service vault -d prod --prefix myapp/prod

# Pull from Vault
enveloper pull --service vault -d prod --prefix myapp/prod
```

### Google Cloud Secret Manager

**Benefits:**
- Integrated with Google Cloud IAM
- Automatic encryption with Google-managed keys
- Secret versioning and rotation
- Audit logging with Cloud Logging

**Configuration:**
```toml
[enveloper.gcp]
project = "my-gcp-project"  # or set GOOGLE_CLOUD_PROJECT
```

**Authentication:**
- Application Default Credentials
- Service account JSON
- Workload Identity (GKE)

**Usage:**
```bash
# Push to Secret Manager
enveloper push --service gcp -d prod --prefix myapp-prod

# Pull from Secret Manager
enveloper pull --service gcp -d prod --prefix myapp-prod
```

### Azure Key Vault

**Benefits:**
- Integrated with Azure Active Directory
- Hardware Security Module (HSM) support
- Soft delete and purge protection
- Key rotation policies

**Configuration:**
```toml
[enveloper.azure]
vault_url = "https://my-vault.vault.azure.net/"  # or set AZURE_VAULT_URL
```

**Authentication:**
- DefaultAzureCredential
- Service principal
- Managed identity

**Usage:**
```bash
# Push to Key Vault
enveloper push --service azure -d prod --prefix myapp-prod

# Pull from Key Vault
enveloper pull --service azure -d prod --prefix myapp-prod
```

### Alibaba Cloud KMS Secrets Manager

**Benefits:**
- Integrated with Alibaba Cloud RAM
- Hardware Security Module support
- Audit logging with ActionTrail
- Secret rotation policies

**Configuration:**
```toml
[enveloper.aliyun]
region_id = "cn-hangzhou"  # or set ALIBABA_CLOUD_REGION_ID
access_key_id = "..."  # or set ALIBABA_CLOUD_ACCESS_KEY_ID
access_key_secret = "..."  # or set ALIBABA_CLOUD_ACCESS_KEY_SECRET
```

**Usage:**
```bash
# Push to KMS Secrets Manager
enveloper push --service aliyun -d prod --prefix myapp-prod

# Pull from KMS Secrets Manager
enveloper pull --service aliyun -d prod --prefix myapp-prod
```

## Push/Pull Workflows

### From Local to Cloud
```bash
# Push from local keychain to cloud
enveloper push --service aws -d prod --prefix /myapp/prod/

# Push from file to cloud
enveloper push --service aws --from file --path .env
```

### From Cloud to Local
```bash
# Pull from cloud to local keychain
enveloper pull --service aws -d prod --prefix /myapp/prod/

# Pull from cloud to file
enveloper pull --service aws --to file --path .env
```

### Cross-Cloud Migration
```bash
# Pull from one cloud, push to another
enveloper pull --service aws -d prod --prefix /app/
enveloper push --service gcp -d prod --prefix app
```

## Security Best Practices

1. **Use IAM policies** - Grant least privilege access
2. **Enable encryption** - Use KMS/HSM for key encryption
3. **Audit access** - Enable logging and monitor access
4. **Rotate secrets** - Regularly update credentials
5. **Use versioning** - Maintain history for rollback
6. **Enable soft delete** - Prevent accidental permanent deletion

## Cost Considerations

| Service | Free Tier | Pricing Model |
|---------|-----------|---------------|
| AWS SSM | 10,000 parameters/month | $0.05 per 10,000 requests |
| GitHub Secrets | Unlimited | Free (included with repo) |
| Vault | Self-hosted | Enterprise pricing |
| GCP Secret Manager | 10,000 operations/month | $0.03 per 10,000 operations |
| Azure Key Vault | 10,000 transactions/month | $0.03 per 10,000 operations |
| Alibaba KMS | Varies | Usage-based |

## Troubleshooting

### AWS SSM
- Check IAM permissions: `ssm:GetParameter`, `ssm:PutParameter`
- Verify region configuration
- Check parameter hierarchy limits

### GitHub Secrets
- Verify repository access
- Check secret name length (max 100 chars)
- Ensure token has `repo` scope

### Vault
- Verify `VAULT_ADDR` and `VAULT_TOKEN`
- Check mount path configuration
- Ensure KV v2 is enabled

### GCP/Azure/Alibaba
- Verify credentials are configured
- Check IAM permissions
- Ensure service is enabled in project