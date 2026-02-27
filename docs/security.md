# Security

## Overview

`enveloper` prioritizes security by storing secrets in encrypted, vendor-provided storage systems. This document outlines the security mechanisms and best practices.

## Local Keychain

### macOS Keychain
- Secrets stored in encrypted keychain database
- Protected by user login password
- Access controlled via Keychain Access app
- No plaintext secrets on disk

### Linux Secret Service
- Uses `libsecret` for secure storage
- Integrates with GNOME Keyring, KWallet, and other secret stores
- Access controlled via system authentication

### Windows Credential Locker
- Uses Windows Data Protection API (DPAPI)
- Secrets encrypted with user's login credentials
- Protected by Windows security subsystem

## Cloud Storage Security

### AWS SSM Parameter Store
- Secrets encrypted with AWS KMS
- Fine-grained IAM access control
- Audit logging via CloudTrail
- Version history for rollback

### Google Cloud Secret Manager
- Secrets encrypted with Google Cloud KMS
- IAM-based access control
- Audit logging via Cloud Logging
- Automatic encryption at rest

### Azure Key Vault
- Secrets encrypted with Key Vault encryption
- Access controlled via Azure RBAC
- Audit logging via Azure Monitor
- Soft-delete and purge protection

### Alibaba Cloud KMS
- Secrets encrypted with KMS
- RAM-based access control
- Audit logging via ActionTrail
- Encryption with customer master keys

### HashiCorp Vault
- Secrets encrypted with configured cipher
- Token-based or certificate authentication
- Audit logging for all operations
- Dynamic secrets support

### GitHub Actions Secrets
- Encrypted at rest
- Access controlled via repository permissions
- Environment protection rules
- Audit logging via GitHub audit log

## Access Control

### IAM Policies
Each cloud provider offers fine-grained access control:

**AWS SSM:**
```json
{
  "Effect": "Allow",
  "Action": [
    "ssm:GetParameter",
    "ssm:GetParameters"
  ],
  "Resource": "arn:aws:ssm:*:*:parameter/envr/*"
}
```

**GCP Secret Manager:**
```json
{
  "role": "roles/secretmanager.secretAccessor",
  "members": ["user:developer@example.com"]
}
```

**Azure Key Vault:**
```json
{
  "permissions": {
    "secrets": ["get", "list"]
  }
}
```

### Least Privilege
- Use separate service accounts for different environments
- Grant only necessary permissions
- Rotate credentials regularly

## Encryption

### At Rest
- Local keychain: OS-native encryption
- Cloud stores: KMS-based encryption
- File storage: Plain text (not recommended for production)

### In Transit
- All cloud stores use HTTPS/TLS
- Local keychain: No network transmission
- File storage: No network transmission

## Best Practices

1. **Use Local Keychain for Development** - Keep secrets local to your machine
2. **Use Cloud Stores for Production** - Enable audit logging and access control
3. **Rotate Credentials Regularly** - Update secrets periodically
4. **Use Environment-Specific Secrets** - Separate dev, staging, prod
5. **Audit Access** - Monitor who accessed secrets and when
6. **Use IAM Policies** - Grant least privilege necessary
7. **Enable Audit Logging** - Track all secret access
8. **Use Versioning** - Keep track of secret changes

## Compliance

### SOC 2
- AWS SSM, GCP Secret Manager, Azure Key Vault are SOC 2 compliant
- Audit logs available for compliance reporting

### HIPAA
- AWS SSM, GCP Secret Manager, Azure Key Vault are HIPAA compliant
- Business Associate Agreements available

### PCI DSS
- Cloud stores support PCI DSS compliance
- Encryption and access control features

## Security Features

| Feature | Local | AWS | GCP | Azure | Alibaba | Vault | GitHub |
|---------|-------|-----|-----|-------|---------|-------|--------|
| Encryption at rest | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Encryption in transit | N/A | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Audit logging | N/A | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Access control | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Versioning | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | N/A |
| Soft-delete | N/A | ✓ | ✓ | ✓ | ✓ | N/A | N/A |