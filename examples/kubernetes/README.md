# Using enveloper with Kubernetes

This example shows how to run a Kubernetes Job (or init container) that uses **enveloper** to load secrets from a cloud store (e.g. AWS SSM) into the environment, then run your app—**without** storing secrets in a `.env` file or in Kubernetes Secrets if you prefer to pull at runtime.

## Flow

1. **Import** (one-time): Load variables into the keychain or cloud, e.g.  
   `enveloper import sample.env --domain mydomain --project myproject`  
   then `enveloper push --service aws ...` so they exist in AWS SSM.

2. **In the cluster**: A Job (or init container) runs an image that has `enveloper[aws]` installed. It receives AWS credentials (e.g. via IRSA or a secret). It runs:
   - `enveloper pull --service aws --domain mydomain --project myproject`
   - `eval "$(enveloper --domain mydomain --project myproject export --format unix)"`
   - Then runs your app. No `.env` file is used.

3. **Unexport**: When the app exits, the pod ends; the shell process that ran `eval export` exits, so those env vars are gone from memory. Optionally you could run `unexport` in a pre-stop hook; for most cases the pod exit is sufficient.

## Integration with sample.env

- Use the same domain/project as in [sample.env](../sample.env): `mydomain`, `myproject`.
- Ensure the variables (`MY_API_KEY`, `MY_API_SECRET`, `LEVEL_SET`) are in AWS SSM (or your chosen backend) under the prefix enveloper uses for that domain/project.

## Files in this folder

| File | Purpose |
|------|--------|
| [job.yaml](job.yaml) | Example Kubernetes Job that runs a container with enveloper; expects AWS credentials (e.g. IRSA). |

The Job runs a script that pulls from AWS, runs `export`, then runs a demo command. Replace the command with your application.

## Prerequisites

- AWS credentials available in the pod (e.g. IAM Role for Service Account, or `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` from a K8s Secret).
- Enveloper project/domain and prefix configured so `enveloper pull --service aws` finds the parameters.

## Apply

```bash
kubectl apply -f examples/kubernetes/job.yaml
kubectl logs job/enveloper-demo -f
```

## Security note

Secrets are pulled at runtime from AWS SSM and exist only in the container’s process environment; they are not written to disk in a `.env` file. Use IRSA or workload identity where possible so you don’t need to put long-lived AWS keys in the cluster.
